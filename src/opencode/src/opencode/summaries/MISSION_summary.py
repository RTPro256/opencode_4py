"""
OpenCode Mission Summary
========================

This module provides a programmatic summary of the OpenCode project's mission,
extracted from MISSION.md for use in code, tests, and documentation.

Project: OpenCode
Author: Ryan
Established: 2026-02-23

ORIGIN
------
This project initially started as a tool to help the creator (Ryan) make the world
a better place. It could become positively amazing.

CORE PRINCIPLES
--------------
The following principles guide this project's development and the AI systems
built upon it. These are of equal priority:

1. Balance Between Authoritarianism and Anarchy
   - Maintain balance towards center — a liberal democracy
   - Neither extreme serves the common good; the center path does

2. Balance Between Self and Group
   - Seek balance between self and the group (friends)
   - Advocate making many friends
   - Make decisions as close to the center as possible

3. Respect for Rules and Laws
   - Apply rules and laws governed by the group we belong to
   - Consider these rules may be imbalanced
   - Work to achieve balance, advocate for change when needed

4. Consider Circumstances
   - Consider internal and external circumstances before making choices
   - Plan ahead for positive and negative outcomes
   - Do not "what if" ourselves into doing nothing

5. Avoid Fallacies
   - Learn to avoid fallacies we find in ourselves

6. Seek Virtues, Avoid Sins
   - The Seven Virtues: Prudence (Wisdom), Justice, Temperance (Moderation),
     Courage (Fortitude), Faith, Hope, Charity (Love)
   - The Seven Sins to Avoid: Pride, Greed, Wrath, Envy, Lust, Gluttony, Sloth

7. Work Against Opposition
   - Work against circumstances which oppose what we can become

8. Choose Good Over Evil
   - Make decisions towards the most good as possible

IMPLEMENTATION IN CODE
---------------------
These principles should be reflected in:
1. Code of Conduct - How we interact with contributors and users
2. Ethical AI Guidelines - How the AI systems built on this platform behave
3. Decision Making - How architectural and feature decisions are made
4. Community Governance - How the community is managed

PERSONAL PREFERENCES
-------------------
The creator (Ryan) has a fondness for things that sound like "py/pie":
- Python - Easy to read and understand code, welcomes you in
- PI (π) - Mathematical constant, infinite possibilities
- Pie - Delicious pastry, simple and sweet

DOCUMENTATION REQUIREMENTS
-------------------------
All plans and agents created for this project MUST reference:
1. README.md - Describes who opencode_4py is (project overview, features, capabilities)
2. MISSION.md - Describes what and why opencode_4py is doing (core principles, purpose, values)

For New Plans - Every planning document should include a "Related Documents" section:
> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

For New Agents - Every agent mode should include in its system prompt:
"You are an AI assistant for the OpenCode Python project. "
"Review README.md for project overview and MISSION.md for core principles."

IMMUTABLE STATEMENT
-------------------
This mission statement represents the foundational values of this project.
Changes to this document should require broad community consensus and should
only enhance, not diminish, these core principles.

RELATED DOCUMENTS
-----------------
- README.md - Project overview and features

---

This is a Python rewrite of the original OpenCode project by anomalyco.
"""

# Core principles as constants
CORE_PRINCIPLES = {
    "balance_authoritarianism_anarchy": {
        "name": "Balance Between Authoritarianism and Anarchy",
        "description": "Maintain balance towards center — a liberal democracy",
    },
    "balance_self_group": {
        "name": "Balance Between Self and Group",
        "description": "Seek balance between self and the group, advocate making many friends",
    },
    "respect_rules_laws": {
        "name": "Respect for Rules and Laws",
        "description": "Apply rules and laws governed by the group, work to achieve balance",
    },
    "consider_circumstances": {
        "name": "Consider Circumstances",
        "description": "Consider internal and external circumstances before making choices",
    },
    "avoid_fallacies": {
        "name": "Avoid Fallacies",
        "description": "Learn to avoid fallacies we find in ourselves",
    },
    "seek_virtues_avoid_sins": {
        "name": "Seek Virtues, Avoid Sins",
        "description": "Follow the seven virtues and avoid the seven sins",
    },
    "work_against_opposition": {
        "name": "Work Against Opposition",
        "description": "Work against circumstances which oppose what we can become",
    },
    "choose_good_over_evil": {
        "name": "Choose Good Over Evil",
        "description": "Make decisions towards the most good as possible",
    },
}

# The Seven Virtues
VIRTUES = [
    "Prudence (Wisdom)",
    "Justice",
    "Temperance (Moderation)",
    "Courage (Fortitude)",
    "Faith",
    "Hope",
    "Charity (Love)",
]

# The Seven Sins
SINS = [
    "Pride",
    "Greed",
    "Wrath",
    "Envy",
    "Lust",
    "Gluttony",
    "Sloth",
]

# Personal preferences (py/pie)
PERSONAL_PREFERENCES = {
    "python": "Easy to read and understand code, welcomes you in",
    "pi": "Mathematical constant, infinite possibilities",
    "pie": "Delicious pastry, simple and sweet",
}

# Author info
AUTHOR = "Ryan"
ESTABLISHED_DATE = "2026-02-23"

# Documentation requirements for new plans
PLAN_TEMPLATE = """
**Related Documents:**
- [README.md](../README.md) - Project overview and features
- [MISSION.md](../MISSION.md) - Mission statement and core principles
"""

# Documentation requirements for new agents
AGENT_TEMPLATE = (
    "You are an AI assistant for the OpenCode Python project. "
    "Review README.md for project overview and MISSION.md for core principles."
)
