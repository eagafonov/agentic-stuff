#!/usr/bin/env python3
"""
GitLab explorer CLI - thin wrapper around python-gitlab.

Authentication via environment variables:
  GITLAB_URL              - GitLab instance URL (e.g. https://gitlab.example.com)
  GITLAB_PRIVATE_TOKEN    - Personal access token

Usage:
  gl.py auth                                     # Verify authentication
  gl.py projects search <query>                  # Search projects
  gl.py project <path> info                      # Project details
  gl.py project <path> mrs [--state STATE] [--author AUTHOR] [--assignee USER] [--reviewer USER] [--scope SCOPE] [--limit N]
  gl.py project <path> mr <mr_iid>               # MR details
  gl.py project <path> mr <mr_iid> changes       # MR diff summary
  gl.py project <path> mr <mr_iid> approvals     # MR approvals
  gl.py project <path> mr <mr_iid> notes [--all] # MR comments (excludes system notes by default)
  gl.py project <path> mr <mr_iid> comment <body> [--file PATH --line N]  # Post MR comment
  gl.py project <path> mr <mr_iid> resolve <note_id>                          # Resolve discussion by note ID
  gl.py project <path> mr <mr_iid> resolve --all                              # Resolve all unresolved discussions
  gl.py project <path> mr <mr_iid> update [--title TITLE] [--description DESC]  # Update MR
  gl.py project <path> commits [--author AUTHOR] [--since DATE] [--until DATE] [--ref REF] [--limit N]
  gl.py project <path> branches [--search PATTERN]
  gl.py project <path> pipelines [--ref REF] [--status STATUS] [--limit N]
  gl.py project <path> issues [--state STATE] [--labels LABELS] [--limit N]
  gl.py events [--after DATE] [--before DATE] [--limit N]   # User activity
  gl.py groups search <query>                    # Search groups
  gl.py group <id> projects [--search QUERY] [--limit N]

Project <path> accepts group/project-name or numeric ID.
Dates are in YYYY-MM-DD format.
"""

import argparse
import json
import os
import sys

import gitlab


def get_client():
    url = os.environ.get("GITLAB_URL") or os.environ.get("GITLAB_API_URL")
    token = os.environ.get("GITLAB_PRIVATE_TOKEN") or os.environ.get(
        "GITLAB_PERSONAL_ACCESS_TOKEN"
    )
    if not url or not token:
        print(
            "Error: GITLAB_URL and GITLAB_PRIVATE_TOKEN must be set", file=sys.stderr
        )
        sys.exit(1)
    return gitlab.Gitlab(url=url, private_token=token)


def fmt_date(d):
    if d is None:
        return ""
    if isinstance(d, str):
        return d[:10]
    return d.isoformat()[:10]


def jprint(obj):
    """Print object as formatted JSON."""
    if hasattr(obj, "attributes"):
        obj = obj.attributes
    print(json.dumps(obj, indent=2, default=str))


# -- Commands --


def cmd_auth(args):
    gl = get_client()
    gl.auth()
    u = gl.user
    print(f"Authenticated as: {u.username} ({u.name})")
    print(f"URL: {gl.url}")
    print(f"API version: {gl.api_version}")


def cmd_projects_search(args):
    gl = get_client()
    projects = gl.projects.list(search=args.query, order_by="last_activity_at", get_all=False, per_page=args.limit)
    for p in projects:
        print(f"{p.id:>10}  {p.path_with_namespace:<60}  {fmt_date(p.last_activity_at)}")


def cmd_project_info(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    jprint({
        "id": p.id,
        "name": p.name,
        "path_with_namespace": p.path_with_namespace,
        "description": p.description,
        "web_url": p.web_url,
        "default_branch": p.default_branch,
        "created_at": p.created_at,
        "last_activity_at": p.last_activity_at,
    })


def cmd_project_mrs(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    kwargs = {"state": args.state, "per_page": args.limit, "get_all": False, "order_by": "updated_at"}
    if args.author:
        kwargs["author_username"] = args.author
    if args.assignee:
        kwargs["assignee_username"] = args.assignee
    if args.reviewer:
        kwargs["reviewer_username"] = args.reviewer
    if args.scope:
        kwargs["scope"] = args.scope
    mrs = p.mergerequests.list(**kwargs)
    for mr in mrs:
        print(f"!{mr.iid:<6} {mr.state:<8} {mr.author['username']:<16} {mr.title}")


def cmd_project_mr_detail(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    mr = p.mergerequests.get(args.mr_iid)
    jprint({
        "iid": mr.iid,
        "title": mr.title,
        "state": mr.state,
        "author": mr.author["username"],
        "source_branch": mr.source_branch,
        "target_branch": mr.target_branch,
        "web_url": mr.web_url,
        "created_at": mr.created_at,
        "updated_at": mr.updated_at,
        "merged_at": getattr(mr, "merged_at", None),
        "description": mr.description,
        "labels": mr.labels,
    })


def cmd_project_mr_changes(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    mr = p.mergerequests.get(args.mr_iid)
    changes = mr.changes()
    for c in changes.get("changes", []):
        old = c.get("old_path", "")
        new = c.get("new_path", "")
        path = new if old == new else f"{old} -> {new}"
        new_file = c.get("new_file", False)
        deleted = c.get("deleted_file", False)
        renamed = c.get("renamed_file", False)
        flag = "A" if new_file else "D" if deleted else "R" if renamed else "M"
        print(f"  {flag}  {path}")


def cmd_project_mr_approvals(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    mr = p.mergerequests.get(args.mr_iid)
    approvals = mr.approvals.get()
    jprint({
        "approved": approvals.approved,
        "approvals_required": approvals.approvals_required,
        "approvals_left": approvals.approvals_left,
        "approved_by": [a["user"]["username"] for a in approvals.approved_by],
    })


def cmd_project_mr_notes(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    mr = p.mergerequests.get(args.mr_iid)
    notes = mr.notes.list(sort="asc", per_page=100, get_all=False)
    for n in notes:
        if n.system and not args.all:
            continue
        author = n.author["username"] if isinstance(n.author, dict) else str(n.author)
        note_type = n.type or "Note"
        resolved = ""
        if hasattr(n, "resolvable") and n.resolvable:
            resolved = " [resolved]" if n.resolved else " [unresolved]"
        # Show file path for DiffNotes
        position_info = ""
        if note_type == "DiffNote" and hasattr(n, "position") and n.position:
            pos = n.position
            path = pos.get("new_path") or pos.get("old_path") or ""
            line = pos.get("new_line") or pos.get("old_line") or ""
            if path:
                position_info = f" ({path}:{line})" if line else f" ({path})"
        header = f"--- #{n.id} {author} {fmt_date(n.created_at)} {note_type}{resolved}{position_info} ---"
        print(header)
        print(n.body)
        print()


def cmd_project_mr_resolve(args):
    """Resolve MR discussion(s) by note ID or all at once."""
    gl = get_client()
    p = gl.projects.get(args.project)
    mr = p.mergerequests.get(args.mr_iid)

    note_id = args.body
    resolve_all = args.all

    if not note_id and not resolve_all:
        print("Error: provide a note_id or --all to resolve all unresolved threads", file=sys.stderr)
        sys.exit(1)

    discussions = mr.discussions.list(get_all=True)
    resolved_count = 0

    for d in discussions:
        notes = d.attributes.get("notes", [])
        # Skip non-resolvable discussions (system notes, general comments)
        if not any(n.get("resolvable") for n in notes):
            continue

        if resolve_all:
            if any(not n.get("resolved", True) for n in notes if n.get("resolvable")):
                d.resolved = True
                d.save()
                resolved_count += 1
                print(f"Resolved discussion {d.id}")
        else:
            if any(str(n["id"]) == str(note_id) for n in notes):
                d.resolved = True
                d.save()
                resolved_count += 1
                print(f"Resolved discussion {d.id} (containing note #{note_id})")
                break

    if resolved_count == 0:
        if resolve_all:
            print("No unresolved discussions found")
        else:
            print(f"Note #{note_id} not found in any resolvable discussion", file=sys.stderr)
            sys.exit(1)


def cmd_project_mr_update(args):
    """Update MR title and/or description."""
    gl = get_client()
    p = gl.projects.get(args.project)
    mr = p.mergerequests.get(args.mr_iid)
    if not args.title and args.description is None:
        print("Error: at least one of --title or --description is required", file=sys.stderr)
        sys.exit(1)
    if args.title:
        mr.title = args.title
    if args.description is not None:
        mr.description = args.description
    mr.save()
    print(f"Updated MR !{mr.iid}")
    if args.title:
        print(f"  title: {mr.title}")
    if args.description is not None:
        desc = mr.description or ""
        desc_preview = desc[:80] + "..." if len(desc) > 80 else desc
        print(f"  description: {desc_preview}")


def cmd_project_mr_comment(args):
    """Post a comment on an MR. Supports general comments and diff notes."""
    gl = get_client()
    p = gl.projects.get(args.project)
    mr = p.mergerequests.get(args.mr_iid)

    body = args.body

    # Read body from stdin if "-" is passed
    if body == "-":
        body = sys.stdin.read()

    if bool(args.file) != bool(args.line):
        print("Error: --file and --line must be used together", file=sys.stderr)
        sys.exit(1)

    if args.file and args.line:
        # Post a diff note on a specific file/line
        diff_refs = mr.diff_refs
        position = {
            "base_sha": diff_refs["base_sha"],
            "start_sha": diff_refs["start_sha"],
            "head_sha": diff_refs["head_sha"],
            "position_type": "text",
            "new_path": args.file,
            "old_path": args.file,
            "new_line": args.line,
        }
        note = mr.discussions.create({"body": body, "position": position})
        note_id = note.attributes["notes"][0]["id"]
        print(f"Created diff note #{note_id} on {args.file}:{args.line}")
    else:
        # Post a general MR comment
        note = mr.notes.create({"body": body})
        print(f"Created note #{note.id}")


def cmd_project_commits(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    kwargs = {"per_page": args.limit, "get_all": False}
    if args.author:
        kwargs["author"] = args.author
    if args.since:
        kwargs["since"] = args.since + "T00:00:00Z"
    if args.until:
        kwargs["until"] = args.until + "T23:59:59Z"
    if args.ref:
        kwargs["ref_name"] = args.ref
    commits = p.commits.list(**kwargs)
    for c in commits:
        print(f"{c.short_id}  {fmt_date(c.created_at)}  {c.author_name:<20}  {c.title}")


def cmd_project_branches(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    kwargs = {"per_page": 50, "get_all": False}
    if args.search:
        kwargs["search"] = args.search
    branches = p.branches.list(**kwargs)
    for b in branches:
        commit_date = fmt_date(b.commit["committed_date"]) if b.commit else ""
        print(f"  {b.name:<50}  {commit_date}")


def cmd_project_pipelines(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    kwargs = {"per_page": args.limit, "get_all": False, "order_by": "updated_at", "sort": "desc"}
    if args.ref:
        kwargs["ref"] = args.ref
    if args.status:
        kwargs["status"] = args.status
    pipelines = p.pipelines.list(**kwargs)
    for pl in pipelines:
        print(f"#{pl.id:<10} {pl.status:<10} {pl.ref:<30} {fmt_date(pl.updated_at)}")


def cmd_project_issues(args):
    gl = get_client()
    p = gl.projects.get(args.project)
    kwargs = {"state": args.state, "per_page": args.limit, "get_all": False, "order_by": "updated_at"}
    if args.labels:
        kwargs["labels"] = args.labels.split(",")
    issues = p.issues.list(**kwargs)
    for i in issues:
        assignee = i.assignee["username"] if i.assignee else ""
        print(f"#{i.iid:<6} {i.state:<8} {assignee:<16} {i.title}")


def cmd_events(args):
    gl = get_client()
    gl.auth()
    kwargs = {"per_page": args.limit, "get_all": False}
    if args.after:
        kwargs["after"] = args.after
    if args.before:
        kwargs["before"] = args.before
    events = gl.events.list(**kwargs)
    for e in events:
        action = e.action_name
        target = getattr(e, "target_title", "") or ""
        target_type = getattr(e, "target_type", "") or ""
        project_id = getattr(e, "project_id", "") or ""
        push_data = getattr(e, "push_data", None)
        if push_data:
            ref = push_data.get("ref", "")
            commit_title = push_data.get("commit_title", "")
            print(f"{fmt_date(e.created_at)}  {action:<20} proj:{project_id}  {ref}  {commit_title}")
        else:
            print(f"{fmt_date(e.created_at)}  {action:<20} proj:{project_id}  {target_type}: {target}")


def cmd_groups_search(args):
    gl = get_client()
    groups = gl.groups.list(search=args.query, per_page=args.limit, get_all=False)
    for g in groups:
        print(f"{g.id:>10}  {g.full_path:<60}  {g.description or ''}")


def cmd_group_projects(args):
    gl = get_client()
    g = gl.groups.get(args.group)
    kwargs = {"per_page": args.limit, "get_all": False, "order_by": "last_activity_at", "include_subgroups": True}
    if args.search:
        kwargs["search"] = args.search
    projects = g.projects.list(**kwargs)
    for p in projects:
        print(f"{p.id:>10}  {p.path_with_namespace:<60}  {fmt_date(getattr(p, 'last_activity_at', ''))}")


def main():
    parser = argparse.ArgumentParser(description="GitLab Explorer CLI", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = parser.add_subparsers(dest="command")

    # auth
    sub.add_parser("auth", help="Verify authentication")

    # projects search
    ps = sub.add_parser("projects", help="Project operations")
    ps_sub = ps.add_subparsers(dest="projects_cmd")
    pss = ps_sub.add_parser("search")
    pss.add_argument("query")
    pss.add_argument("--limit", type=int, default=20)

    # project <id> ...
    proj = sub.add_parser("project", help="Single project operations")
    proj.add_argument("project", help="Project path (group/name) or numeric ID")
    proj_sub = proj.add_subparsers(dest="project_cmd")

    proj_sub.add_parser("info")

    mrs_p = proj_sub.add_parser("mrs")
    mrs_p.add_argument("--state", default="opened", choices=["opened", "closed", "merged", "all"])
    mrs_p.add_argument("--author", default=None)
    mrs_p.add_argument("--assignee", default=None)
    mrs_p.add_argument("--reviewer", default=None)
    mrs_p.add_argument("--scope", default=None, choices=["created_by_me", "assigned_to_me", "all"])
    mrs_p.add_argument("--limit", type=int, default=20)

    mr_p = proj_sub.add_parser("mr")
    mr_p.add_argument("mr_iid", type=int)
    mr_p.add_argument("mr_subcmd", nargs="?", choices=["changes", "approvals", "notes", "comment", "resolve", "update"], default=None)
    mr_p.add_argument("--all", action="store_true", help="Include system notes (for 'notes' subcommand)")
    mr_p.add_argument("body", nargs="?", default=None, help="Comment body (for 'comment' subcommand, use '-' for stdin)")
    mr_p.add_argument("--file", default=None, help="File path for diff note")
    mr_p.add_argument("--line", type=int, default=None, help="Line number for diff note")
    mr_p.add_argument("--title", default=None, help="New MR title (for 'update' subcommand)")
    mr_p.add_argument("--description", default=None, help="New MR description (for 'update' subcommand)")

    commits_p = proj_sub.add_parser("commits")
    commits_p.add_argument("--author", default=None)
    commits_p.add_argument("--since", default=None, help="YYYY-MM-DD")
    commits_p.add_argument("--until", default=None, help="YYYY-MM-DD")
    commits_p.add_argument("--ref", default=None)
    commits_p.add_argument("--limit", type=int, default=20)

    br_p = proj_sub.add_parser("branches")
    br_p.add_argument("--search", default=None)

    pl_p = proj_sub.add_parser("pipelines")
    pl_p.add_argument("--ref", default=None)
    pl_p.add_argument("--status", default=None, choices=["running", "pending", "success", "failed", "canceled", "skipped"])
    pl_p.add_argument("--limit", type=int, default=10)

    iss_p = proj_sub.add_parser("issues")
    iss_p.add_argument("--state", default="opened", choices=["opened", "closed", "all"])
    iss_p.add_argument("--labels", default=None, help="Comma-separated labels")
    iss_p.add_argument("--limit", type=int, default=20)

    # events
    ev = sub.add_parser("events", help="User activity events")
    ev.add_argument("--after", default=None, help="YYYY-MM-DD")
    ev.add_argument("--before", default=None, help="YYYY-MM-DD")
    ev.add_argument("--limit", type=int, default=30)

    # groups
    gs = sub.add_parser("groups", help="Group operations")
    gs_sub = gs.add_subparsers(dest="groups_cmd")
    gss = gs_sub.add_parser("search")
    gss.add_argument("query")
    gss.add_argument("--limit", type=int, default=20)

    # group <id> ...
    grp = sub.add_parser("group", help="Single group operations")
    grp.add_argument("group", help="Group ID or path")
    grp_sub = grp.add_subparsers(dest="group_cmd")
    gp = grp_sub.add_parser("projects")
    gp.add_argument("--search", default=None)
    gp.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "auth":
            cmd_auth(args)
        elif args.command == "projects":
            if args.projects_cmd == "search":
                cmd_projects_search(args)
            else:
                ps.print_help()
        elif args.command == "project":
            if args.project_cmd == "info":
                cmd_project_info(args)
            elif args.project_cmd == "mrs":
                cmd_project_mrs(args)
            elif args.project_cmd == "mr":
                if args.mr_subcmd == "changes":
                    cmd_project_mr_changes(args)
                elif args.mr_subcmd == "approvals":
                    cmd_project_mr_approvals(args)
                elif args.mr_subcmd == "notes":
                    cmd_project_mr_notes(args)
                elif args.mr_subcmd == "comment":
                    if not args.body:
                        print("Error: comment body is required (pass text or '-' for stdin)", file=sys.stderr)
                        sys.exit(1)
                    cmd_project_mr_comment(args)
                elif args.mr_subcmd == "resolve":
                    cmd_project_mr_resolve(args)
                elif args.mr_subcmd == "update":
                    cmd_project_mr_update(args)
                else:
                    cmd_project_mr_detail(args)
            elif args.project_cmd == "commits":
                cmd_project_commits(args)
            elif args.project_cmd == "branches":
                cmd_project_branches(args)
            elif args.project_cmd == "pipelines":
                cmd_project_pipelines(args)
            elif args.project_cmd == "issues":
                cmd_project_issues(args)
            else:
                proj.print_help()
        elif args.command == "events":
            cmd_events(args)
        elif args.command == "groups":
            if args.groups_cmd == "search":
                cmd_groups_search(args)
            else:
                gs.print_help()
        elif args.command == "group":
            if args.group_cmd == "projects":
                cmd_group_projects(args)
            else:
                grp.print_help()
    except gitlab.exceptions.GitlabAuthenticationError as e:
        print(f"Authentication error: {e}", file=sys.stderr)
        sys.exit(1)
    except gitlab.exceptions.GitlabGetError as e:
        print(f"GitLab API error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
