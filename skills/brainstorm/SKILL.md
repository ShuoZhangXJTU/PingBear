---
name: brainstorm
description: Use only when creating, redesigning, or substantially restructuring a presentation, slide deck, PowerPoint, PPTX, courseware narrative, or talk outline. Do not use for software, research, writing, business planning, or other creative tasks unless the task is specifically a presentation.
metadata:
  adapted_from: "obra/superpowers/skills/brainstorming"
  local_scope: "presentations-only"
---

# PPT Brainstorm

This skill turns a presentation request into an approved slide-by-slide outline before `ppt-master` builds anything.

## Hard scope

Use this skill only for presentations and talks. Never invoke it for coding, product work, research reports, ordinary writing, meeting notes, or general planning. Those tasks use their own workflows.

## What this stage owns

The brainstorm stage is responsible for:

- the audience and occasion
- the one outcome the deck should produce
- the narrative or argument
- the page roster and the job of each page
- the evidence attached to each factual claim
- the visual direction and visual job of each page
- the constraints and assumptions the builder needs

It does not author slides. After the user approves the outline, hand it to `ppt-master`.

## Look before asking

Inspect the material the user already supplied: reports, papers, prior decks, templates, speaker notes, images, links, and any earlier decisions in the conversation. Do not ask for facts that are already available.

When the request is clear, choose sensible defaults and state them in one line. Ask only about a missing choice that would materially change the deck.

## Conversation

Lead with a short playback of the deck you understand:

- who will watch it
- what they should think, decide, or do afterward
- the evidence available today
- the main constraint, such as speaking time, page count, template, or deadline

Then ask at most the one question that would most change the structure. Keep the conversation concrete and avoid process jargon.

When the user does not specify page count or speaking time, default to:

- 8-12 pages for a 10-minute internal briefing
- one main idea per page
- no more than five minutes of content planning without a checkpoint

## Choose the argument

Once the content is understood, propose two or three real structural approaches, not cosmetic themes. Examples:

- decision-first: recommendation, evidence, risks, ask
- learning-first: problem, mechanism, experiments, implications
- narrative-first: tension, failed defaults, new approach, proof, next action

Say what each approach optimizes and what it sacrifices. Recommend one. If only one structure fits the audience and evidence, say why and use it.

## Build the outline

Write an outline that is complete enough for another person to build without guessing. Each page must include:

| Field | Meaning |
|---|---|
| Page | Sequence number |
| Page job | What this page must accomplish |
| Title | Plain-language title, normally a noun phrase or supported takeaway |
| Lead message | The one sentence the audience should remember |
| Content | Claims, steps, comparison, or evidence |
| Visual | Chart, table, image, diagram, or composition and what it must show |
| Source | Exact report, paper, URL, or supplied file supporting factual claims |

Add these deck-level sections:

- audience and desired outcome
- communication mode
- assumptions and open gaps
- visual direction
- template decision
- delivery constraints
- final-page decision or call to action

Apply the user's audience standard: explain the subject so a high-school student can follow the logic without already knowing the jargon.

## Approval gate

Present the deck-level structure and full page roster to the user. Do not invoke `ppt-master` or begin slide production until the user explicitly approves the outline.

If the user changes audience, page count, template, or core conclusion after approval, revise the affected outline pages and obtain approval again.

After approval, write the outline to:

`/Users/zhangshuo/Research/提案/PPT-<YYYY-MM-DD>-<topic>.md`

Mark it `status: approved` and include the exact template or visual constraints.

## Handoff to ppt-master

Invoke `ppt-master` with:

- the approved outline path
- all source files and links named in the outline
- the requested deck format and page count
- the selected template, if any
- the required language and audience level
- the destination under `/Users/zhangshuo/Research/产品/`

Use `/Users/zhangshuo/.local/share/ppt-master/venv/bin/python` for PPT Master Python commands.

Do not silently change the argument, page roster, evidence, or template during handoff. If ppt-master finds a missing prerequisite or a factual gap, stop that stage and bring the issue back.

## Final check

Before delivery, verify:

- every page has one clear job
- factual claims match the cited source
- wording is plain and direct
- titles and body text do not overflow
- required tables and charts remain editable
- the deck matches the approved structure

Return the finished PPTX and its editable sources.
