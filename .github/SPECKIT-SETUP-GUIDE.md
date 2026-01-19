# Speckit Slash Commands Setup Guide for GitHub Copilot

This guide explains how to add the speckit slash commands to GitHub Copilot in your IDE.

## Overview

The speckit framework provides specialized agents for spec-driven development:

- `/speckit.specify` - Create feature specifications
- `/speckit.plan` - Create implementation plans
- `/speckit.tasks` - Generate task lists
- `/speckit.implement` - Execute implementation tasks
- `/speckit.analyze` - Analyze consistency across artifacts
- `/speckit.checklist` - Generate verification checklists
- `/speckit.clarify` - Clarify requirements
- `/speckit.constitution` - Manage project principles
- `/speckit.taskstoissues` - Convert tasks to GitHub issues

## Setup Instructions

### Method 1: VS Code with GitHub Copilot Extension

1. **Open VS Code Settings** (Ctrl/Cmd + ,)

2. **Navigate to GitHub Copilot Chat Agent Settings**:
   - Search for: `github.copilot.chat.codeGeneration.instructions`
   - Or go to: Extensions → GitHub Copilot → Extension Settings

3. **Add Agent Files**:
   - Click "Edit in settings.json"
   - Add the agent configurations:

   ```json
   {
     "github.copilot.chat.codeGeneration.instructions": [
       {
         "file": ".github/agents/speckit.specify.agent.md"
       },
       {
         "file": ".github/agents/speckit.plan.agent.md"
       },
       {
         "file": ".github/agents/speckit.tasks.agent.md"
       },
       {
         "file": ".github/agents/speckit.implement.agent.md"
       },
       {
         "file": ".github/agents/speckit.analyze.agent.md"
       },
       {
         "file": ".github/agents/speckit.checklist.agent.md"
       },
       {
         "file": ".github/agents/speckit.clarify.agent.md"
       },
       {
         "file": ".github/agents/speckit.constitution.agent.md"
       },
       {
         "file": ".github/agents/speckit.taskstoissues.agent.md"
       }
     ]
   }
   ```

4. **Reload VS Code**:
   - Press Ctrl/Cmd + Shift + P
   - Type "Reload Window"
   - Select "Developer: Reload Window"

5. **Verify Installation**:
   - Open Copilot Chat (Ctrl/Cmd + Shift + I)
   - Type `/` and you should see the speckit commands in the autocomplete

### Method 2: JetBrains IDEs (IntelliJ, PyCharm, etc.)

1. **Open Settings** (Ctrl/Cmd + Alt + S)

2. **Navigate to GitHub Copilot Settings**:
   - Go to: Tools → GitHub Copilot

3. **Configure Agent Files**:
   - Look for "Custom Instructions" or "Agent Configuration"
   - Add references to the `.github/agents/*.agent.md` files

4. **Restart IDE**

### Method 3: Via Copilot Instructions File

If your IDE supports loading instructions from `.github/copilot-instructions.md`, you can add agent references there:

1. **Edit `.github/copilot-instructions.md`**:

   ```markdown
   # Project-Specific Copilot Instructions

   ## Available Agents

   This project uses the speckit framework for spec-driven development.

   ### Agent Files

   - `.github/agents/speckit.specify.agent.md` - Feature specification creation
   - `.github/agents/speckit.plan.agent.md` - Implementation planning
   - `.github/agents/speckit.tasks.agent.md` - Task list generation
   - `.github/agents/speckit.implement.agent.md` - Task implementation
   - `.github/agents/speckit.analyze.agent.md` - Artifact analysis
   - `.github/agents/speckit.checklist.agent.md` - Verification checklists
   - `.github/agents/speckit.clarify.agent.md` - Requirement clarification
   - `.github/agents/speckit.constitution.agent.md` - Project principles
   - `.github/agents/speckit.taskstoissues.agent.md` - GitHub issue creation

   ## Usage

   Use slash commands in Copilot Chat:
   - `/speckit.specify <feature description>` - Start a new feature spec
   - `/speckit.plan` - Create implementation plan from spec
   - `/speckit.tasks` - Generate tasks from plan
   - `/speckit.implement` - Execute next task
   - `/speckit.analyze` - Check consistency
   ```

2. **Reload Copilot**

## Using Speckit Commands

### Basic Workflow

1. **Create Specification**:
   ```
   /speckit.specify Add pagination to email list with subject display
   ```

2. **Create Implementation Plan**:
   ```
   /speckit.plan
   ```

3. **Generate Tasks**:
   ```
   /speckit.tasks
   ```

4. **Analyze Artifacts**:
   ```
   /speckit.analyze
   ```

5. **Implement Tasks**:
   ```
   /speckit.implement
   ```

### Command Details

#### `/speckit.specify`
Creates a feature specification with user stories, requirements, and success criteria.

**Usage**: `/speckit.specify <feature description>`

**Example**: `/speckit.specify Add Gmail label filtering and pagination to email list`

#### `/speckit.plan`
Creates an implementation plan based on the specification.

**Usage**: `/speckit.plan`

**Prerequisites**: Must have `spec.md` in current feature branch

#### `/speckit.tasks`
Generates a task list for implementation.

**Usage**: `/speckit.tasks`

**Prerequisites**: Must have `spec.md` and `plan.md`

#### `/speckit.implement`
Executes the next task from the task list.

**Usage**: `/speckit.implement`

**Prerequisites**: Must have `tasks.md`

#### `/speckit.analyze`
Analyzes consistency across spec, plan, and tasks.

**Usage**: `/speckit.analyze`

**Prerequisites**: Must have `spec.md`, `plan.md`, and `tasks.md`

## Directory Structure

The speckit framework expects this structure:

```
your-project/
├── .github/
│   ├── agents/                  # Agent definition files
│   │   ├── speckit.specify.agent.md
│   │   ├── speckit.plan.agent.md
│   │   ├── speckit.tasks.agent.md
│   │   ├── speckit.implement.agent.md
│   │   └── ...
│   └── copilot-instructions.md  # Project-specific instructions
├── .specify/
│   ├── memory/                  # Project memory
│   │   └── constitution.md      # Project principles
│   ├── scripts/                 # Helper scripts
│   │   └── bash/
│   └── templates/               # Document templates
├── specs/                       # Feature specifications
│   └── XXX-feature-name/        # Feature directory
│       ├── spec.md              # Feature specification
│       ├── plan.md              # Implementation plan
│       ├── tasks.md             # Task list
│       └── checklists/          # Verification checklists
└── src/                         # Source code
```

## Troubleshooting

### Commands Don't Appear in Autocomplete

1. **Check file paths**: Ensure `.github/agents/*.agent.md` files exist
2. **Reload IDE**: Restart VS Code or your IDE completely
3. **Check Copilot version**: Update GitHub Copilot extension to latest version
4. **Check permissions**: Ensure agent files are readable

### Commands Don't Work

1. **Check prerequisites**: Run the prerequisite scripts manually:
   ```bash
   .specify/scripts/bash/check-prerequisites.sh --json
   ```

2. **Check branch**: Ensure you're on a feature branch (XXX-feature-name format)

3. **Check file existence**: Ensure required files exist:
   - `spec.md` for `/speckit.plan`
   - `plan.md` for `/speckit.tasks`
   - `tasks.md` for `/speckit.implement`

### Agent Files Not Loading

1. **Check file format**: Ensure agent files are valid Markdown
2. **Check frontmatter**: Agent files should have YAML frontmatter with description
3. **Check paths**: Use relative paths from repository root

## Additional Resources

- **Agent Files**: See `.github/agents/` for individual agent definitions
- **Templates**: See `.specify/templates/` for document templates
- **Scripts**: See `.specify/scripts/bash/` for helper scripts
- **Constitution**: See `.specify/memory/constitution.md` for project principles

## Support

If you encounter issues:

1. Check the agent file for specific instructions
2. Run prerequisite checks manually
3. Check IDE logs for Copilot errors
4. Verify file paths and permissions

---

**Last Updated**: 2025-01-19
**Speckit Version**: 1.0 (based on repository structure)
