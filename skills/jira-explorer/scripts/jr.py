#!/usr/bin/env python3
"""
Jira explorer CLI - thin wrapper around python-jira.

Authentication via environment variables:
  JIRA_URL        - Jira instance URL (e.g. https://jira.example.com)
  JIRA_HOST       - Jira hostname (e.g. jira.example.com); used as
                    https://<JIRA_HOST> when JIRA_URL is not set
  JIRA_API_TOKEN  - Personal Access Token (Data Center 8.14+)

Usage:
  jr.py auth                                      # Verify authentication
  jr.py myself [--limit N]                        # Current user + assigned issues
  jr.py search <JQL> [--limit N]                  # Run JQL query
  jr.py issue <KEY>                               # Issue details (JSON)
  jr.py issue <KEY> comments                      # List comments
  jr.py issue <KEY> comment <body>                # Post comment (use '-' for stdin)
  jr.py issue <KEY> transitions                   # List available transitions
  jr.py issue <KEY> transition <name>             # Move issue to new status
  jr.py issue <KEY> update <field=value>... [--json '{}']  # Update fields

Issue <KEY> is the full issue key (e.g. PROJ-123).
"""

import argparse
import json
import os
import sys

from jira import JIRA, JIRAError


def _resolve_url():
    """Resolve Jira server URL from JIRA_URL or JIRA_HOST."""
    url = os.environ.get("JIRA_URL")
    if url:
        return url.rstrip("/")
    host = os.environ.get("JIRA_HOST")
    if host:
        # Strip accidental scheme/slashes so we always build a clean URL
        host = host.strip("/")
        if host.startswith(("http://", "https://")):
            return host.rstrip("/")
        return f"https://{host}"
    return None


def get_client():
    """Create authenticated Jira client from environment variables."""
    url = _resolve_url()
    token = os.environ.get("JIRA_API_TOKEN")
    if not url or not token:
        print("Error: JIRA_URL (or JIRA_HOST) and JIRA_API_TOKEN must be set", file=sys.stderr)
        sys.exit(1)
    return JIRA(server=url, token_auth=token)


def jprint(obj):
    """Print object as formatted JSON."""
    print(json.dumps(obj, indent=2, default=str))


# -- Commands --


def cmd_auth(args):
    """Verify authentication and print user info."""
    client = get_client()
    myself = client.myself()
    server_info = client.server_info()
    jprint({
        "username": myself.get("name", ""),
        "displayName": myself.get("displayName", ""),
        "emailAddress": myself.get("emailAddress", ""),
        "serverUrl": _resolve_url(),
        "serverVersion": server_info.get("version", ""),
        "serverTitle": server_info.get("serverTitle", ""),
    })


def cmd_myself(args):
    """Show current user info and assigned issues."""
    client = get_client()
    myself = client.myself()
    username = myself.get("name", "")
    print(f"User: {username} ({myself.get('displayName', '')})")
    print(f"Email: {myself.get('emailAddress', '')}")
    print()

    jql = "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC"
    issues = client.search_issues(jql, maxResults=args.limit)
    print(f"Open issues assigned to me ({len(issues)}):")
    for issue in issues:
        key = issue.key
        status = str(issue.fields.status)
        summary = issue.fields.summary
        print(f"  {key:<12} {status:<16} {summary}")


def cmd_search(args):
    """Run JQL query and display results."""
    client = get_client()
    issues = client.search_issues(args.jql, maxResults=args.limit)
    for issue in issues:
        key = issue.key
        status = str(issue.fields.status)
        assignee = str(issue.fields.assignee) if issue.fields.assignee else ""
        summary = issue.fields.summary
        print(f"{key:<12} {status:<16} {assignee:<20} {summary}")


def cmd_issue_detail(args):
    """Show issue details as JSON."""
    client = get_client()
    issue = client.issue(args.key)
    f = issue.fields
    jprint({
        "key": issue.key,
        "summary": f.summary,
        "status": str(f.status),
        "issueType": str(f.issuetype),
        "priority": str(f.priority) if f.priority else None,
        "assignee": str(f.assignee) if f.assignee else None,
        "reporter": str(f.reporter) if f.reporter else None,
        "labels": f.labels or [],
        "created": f.created,
        "updated": f.updated,
        "resolved": f.resolutiondate,
        "description": f.description,
    })


def cmd_issue_comments(args):
    """List comments on an issue."""
    client = get_client()
    issue = client.issue(args.key)
    comments = client.comments(issue)
    if not comments:
        print("No comments.")
        return
    for c in comments:
        author = c.author.displayName if hasattr(c, "author") else "Unknown"
        created = c.created[:10] if c.created else ""
        print(f"--- #{c.id} {author} {created} ---")
        print(c.body)
        print()


def cmd_issue_comment(args):
    """Post a comment on an issue."""
    client = get_client()
    body = args.body
    if body == "-":
        body = sys.stdin.read()
    if not body:
        print("Error: comment body is required (pass text or '-' for stdin)", file=sys.stderr)
        sys.exit(1)
    client.add_comment(args.key, body)
    print(f"Comment added to {args.key}")


def cmd_issue_transitions(args):
    """List available transitions for an issue."""
    client = get_client()
    transitions = client.transitions(args.key)
    for t in transitions:
        print(f"  {t['id']:<6} {t['name']}")


def cmd_issue_transition(args):
    """Transition an issue to a new status."""
    client = get_client()
    name = args.body
    if not name:
        print("Error: transition name is required", file=sys.stderr)
        sys.exit(1)

    transitions = client.transitions(args.key)
    # Case-insensitive match
    match = None
    for t in transitions:
        if t["name"].lower() == name.lower():
            match = t
            break

    if not match:
        print(f"Error: transition '{name}' not found. Available transitions:", file=sys.stderr)
        for t in transitions:
            print(f"  {t['id']:<6} {t['name']}", file=sys.stderr)
        sys.exit(1)

    client.transition_issue(args.key, match["id"])
    print(f"Transitioned {args.key} -> {match['name']}")


def cmd_issue_update(args):
    """Update issue fields."""
    client = get_client()
    fields = {}

    # Parse field=value positional args
    for pair in args.fields:
        if "=" not in pair:
            print(f"Error: invalid field format '{pair}', expected field=value", file=sys.stderr)
            sys.exit(1)
        key, value = pair.split("=", 1)
        fields[key] = value

    # Parse --json if provided
    if args.json_fields:
        try:
            json_data = json.loads(args.json_fields)
            fields.update(json_data)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    if not fields:
        print("Error: at least one field=value or --json is required", file=sys.stderr)
        sys.exit(1)

    issue = client.issue(args.key)
    issue.update(fields=fields)
    print(f"Updated {args.key}:")
    for k, v in fields.items():
        val_str = str(v)
        if len(val_str) > 80:
            val_str = val_str[:80] + "..."
        print(f"  {k} = {val_str}")


# -- Argument Parsing --


def parse_issue_args(argv):
    """Parse issue subcommand arguments.

    argv is everything after 'issue' in sys.argv.
    """
    if not argv:
        print("Error: issue key is required", file=sys.stderr)
        print("Usage: jr.py issue <KEY> [comments|comment|transitions|transition|update]", file=sys.stderr)
        sys.exit(1)

    key = argv[0]
    subcmd = argv[1] if len(argv) > 1 else None
    rest = argv[2:]

    ns = argparse.Namespace(command="issue", key=key, subcmd=subcmd, limit=20)

    if subcmd in ("comment", "transition"):
        ns.body = " ".join(rest) if rest else None
        ns.fields = []
        ns.json_fields = None
    elif subcmd == "update":
        # Separate --json from field=value pairs
        ns.json_fields = None
        ns.fields = []
        ns.body = None
        i = 0
        while i < len(rest):
            if rest[i] == "--json" and i + 1 < len(rest):
                ns.json_fields = rest[i + 1]
                i += 2
            else:
                ns.fields.append(rest[i])
                i += 1
    else:
        ns.body = None
        ns.fields = []
        ns.json_fields = None

    return ns


def main():
    # Handle 'issue' command with manual parsing for flexibility
    if len(sys.argv) > 1 and sys.argv[1] == "issue":
        args = parse_issue_args(sys.argv[2:])
    else:
        parser = argparse.ArgumentParser(
            description="Jira Explorer CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=__doc__,
        )
        sub = parser.add_subparsers(dest="command")

        # auth
        sub.add_parser("auth", help="Verify authentication")

        # myself
        myself_p = sub.add_parser("myself", help="Current user + assigned issues")
        myself_p.add_argument("--limit", type=int, default=20)

        # search
        search_p = sub.add_parser("search", help="Run JQL query")
        search_p.add_argument("jql", help="JQL query string")
        search_p.add_argument("--limit", type=int, default=20)

        # issue (placeholder for help text)
        sub.add_parser("issue", help="Issue operations (use: jr.py issue <KEY> [subcmd])")

        args = parser.parse_args()

        if args.command is None:
            parser.print_help()
            sys.exit(1)

    try:
        if args.command == "auth":
            cmd_auth(args)
        elif args.command == "myself":
            cmd_myself(args)
        elif args.command == "search":
            cmd_search(args)
        elif args.command == "issue":
            if args.subcmd is None:
                cmd_issue_detail(args)
            elif args.subcmd == "comments":
                cmd_issue_comments(args)
            elif args.subcmd == "comment":
                cmd_issue_comment(args)
            elif args.subcmd == "transitions":
                cmd_issue_transitions(args)
            elif args.subcmd == "transition":
                cmd_issue_transition(args)
            elif args.subcmd == "update":
                cmd_issue_update(args)
            else:
                print(f"Error: unknown issue subcommand '{args.subcmd}'", file=sys.stderr)
                print("Available: comments, comment, transitions, transition, update", file=sys.stderr)
                sys.exit(1)
    except JIRAError as e:
        text = getattr(e, "text", None) or (e.response.text if hasattr(e, "response") else str(e))
        print(f"Jira API error: {text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
