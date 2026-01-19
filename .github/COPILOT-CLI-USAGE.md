# Using Speckit with GitHub Copilot CLI

## Important Note

GitHub Copilot CLI (terminal) does **not** natively support custom slash commands like VS Code does. However, you can still use the speckit framework by invoking the agents explicitly.

## How to Use Speckit in Copilot CLI

### Method 1: Direct Agent Invocation (Recommended)

Simply type the command name, and I'll recognize it from the copilot-instructions.md file and load the corresponding agent:

```bash
# In your terminal with Copilot CLI
/speckit.specify Add pagination and subject display to Gmail list
```

I will:
1. Recognize the command from `.github/copilot-instructions.md`
2. Load the agent definition from `.github/agents/speckit.specify.agent.md`
3. Execute according to the agent's instructions

### Method 2: Explicit Agent Reference

You can also be explicit about which agent to use:

```bash
# Request the agent directly
Please act as the speckit.specify agent and create a specification for: Add pagination to Gmail list
```

### Method 3: Direct File Reference

Reference the agent file explicitly:

```bash
# Load and execute an agent
Follow the instructions in .github/agents/speckit.plan.agent.md to create an implementation plan
```

## Available Commands

All of these work in Copilot CLI if you mention them:

### Specification Phase
- `/speckit.specify <feature description>` - Create a feature specification
- `/speckit.clarify` - Clarify ambiguous requirements

### Planning Phase
- `/speckit.plan` - Generate implementation plan from spec
- `/speckit.constitution` - Check against project principles

### Implementation Phase
- `/speckit.tasks` - Create task list from plan
- `/speckit.analyze` - Analyze consistency across artifacts
- `/speckit.checklist` - Generate verification checklist

### Execution Phase
- `/speckit.implement` - Execute next task
- `/speckit.taskstoissues` - Convert tasks to GitHub issues

## Example Workflow

```bash
# 1. Create specification
/speckit.specify Add email subject display and label filtering to Gmail list command

# 2. Generate plan (after spec is reviewed)
/speckit.plan

# 3. Generate tasks (after plan is reviewed)
/speckit.tasks

# 4. Analyze for consistency
/speckit.analyze

# 5. Implement first task
/speckit.implement

# 6. Continue implementing
/speckit.implement

# 7. Generate checklist for verification
/speckit.checklist
```

## How It Works

1. **Agent Detection**: The `.github/copilot-instructions.md` file lists all available agents
2. **Agent Loading**: When you mention a command (e.g., `/speckit.plan`), I recognize it and load the agent definition from `.github/agents/speckit.plan.agent.md`
3. **Agent Execution**: I follow the agent's instructions to complete the task

## Context Awareness

I automatically have access to:
- Your project structure (`src/gtool/`)
- Existing specifications (`specs/007-gmail-list-enhancements/`)
- Configuration files (`.github/copilot-instructions.md`)
- Agent definitions (`.github/agents/*.agent.md`)
- Helper scripts (`.specify/scripts/bash/`)

## Tips for Best Results

1. **Be Explicit**: If a command doesn't work as expected, explicitly reference the agent file
2. **Provide Context**: Mention the feature branch or spec directory if applicable
3. **Follow Workflow**: Use agents in order (specify → plan → tasks → implement)
4. **Check Prerequisites**: Each agent has prerequisites (e.g., `/speckit.plan` needs `spec.md`)

## Differences from VS Code

| Feature | VS Code | Copilot CLI |
|---------|---------|-------------|
| Slash command autocomplete | ✅ Yes | ❌ No |
| Custom slash commands | ✅ Native | ⚠️ Via prompt |
| Agent file loading | ✅ Automatic | ✅ On mention |
| Project context | ✅ Full | ✅ Full |
| Interactive workflow | ✅ UI-based | ✅ Chat-based |

## Troubleshooting

### Command Not Recognized

**Problem**: I don't seem to recognize the command

**Solution**:
- Ensure `.github/copilot-instructions.md` is updated with agent list
- Try being more explicit: "Follow the speckit.plan agent instructions"
- Reference the agent file directly: "Use .github/agents/speckit.plan.agent.md"

### Prerequisites Not Met

**Problem**: Agent reports missing files (e.g., "spec.md not found")

**Solution**:
- Check if you're on the correct feature branch
- Verify the file exists in `specs/XXX-feature-name/`
- Run prerequisite check manually:
  ```bash
  .specify/scripts/bash/check-prerequisites.sh --json
  ```

### Agent Behavior Different from VS Code

**Problem**: Agent behaves differently in CLI vs VS Code

**Solution**: Both environments use the same agent files. The behavior should be identical. If not, ensure:
- Both environments use the same agent file versions
- The `.github/copilot-instructions.md` is up to date
- No local VS Code settings override agent behavior

## Advanced Usage

### Custom Instructions

You can combine agent instructions with custom modifications:

```bash
/speckit.specify Add pagination to Gmail list, but focus heavily on performance and large mailbox support
```

### Agent Chaining

Execute multiple agents in sequence:

```bash
First run /speckit.specify for "Add email subjects to list", then immediately run /speckit.plan
```

### Debugging Agents

To see what an agent will do before executing:

```bash
Show me the instructions from .github/agents/speckit.implement.agent.md without executing them
```

## Limitations

1. **No Native Slash Command UI**: Unlike VS Code, Copilot CLI doesn't show slash command autocomplete
2. **Manual Agent Invocation**: You must explicitly mention the command or agent
3. **No Command History**: Unlike VS Code agents, there's no special command history for agents

## Alternatives

If you prefer native slash command support:
1. **Use VS Code**: Open the project in VS Code for full agent support
2. **Use Both**: Use VS Code for specification/planning, CLI for implementation
3. **Create Aliases**: Create shell aliases for common agent invocations

---

**Last Updated**: 2025-01-19
**Note**: This document explains Copilot CLI usage. For VS Code setup, see `.github/SPECKIT-SETUP-GUIDE.md`
