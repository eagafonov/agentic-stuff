# My Agentic Stuff

Random Agentic stuff for daily work as a software developer

## Install skill

```shell
git clone https://github.com/eagafonov/agentic-stuff
cd agentic-stuff
mkdir -p ~/.agents/skills/
ln -s `pwd` ~/.agents/skills/
```

## Install pi prompts

See [pi prompt templates documentation](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/prompt-templates.md) for more details.

```shell
mkdir -p ~/.pi/agent/prompts/
ln -s `pwd`/pi/prompts/*.md ~/.pi/agent/prompts/
```

## Notable references

In no particular order

* [pi-mono](https://github.com/badlogic/pi-mono) and its [coding agent](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent)
    > Tools for building AI agents and managing LLM deployments.

* [pi acp](https://github.com/svkozak/pi-acp)
    > Still MVP but good enough to use pi in my favorite (for now) [editor](https://zed.dev/).

* [agentskills](https://github.com/agentskills/agentskills) [specification](https://agentskills.io/specification)
    > A simple, open format for giving agents new capabilities and expertise.

* [awesome-pi-agent](https://github.com/qualisero/awesome-pi-agent)
    > Concise, curated resources for extending and integrating the pi coding agent.
