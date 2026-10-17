# Delivery-tracker navigation: how rails are ordered for planning and for progress reporting

> Discipline: applied (practitioner-pattern survey)

Surveyed 2026-10-16 to decide how the offline intent view orders its rail once it gains a roadmap question, a done filter, a by-capability grouping and owner filtering. Products: Linear, Asana, Jira (2025 navigation and Plans), GitHub Projects, Shortcut; Height (shut down 2025-09-24) and Notion yielded nothing usable. Most sources are each vendor's own docs, so for triangulation each vendor counts as one source.

## Findings

### 1. Personal "what's mine now" comes first, shared structure after it `[high]`

- Linear's sidebar runs Inbox, My Issues, then Workspace (projects, initiatives, views), then Your teams ([Navigating Linear](https://linear.app/enablement/guide/navigating-linear)).
- Jira's 2025 sidebar runs For you, Recent, Starred, then Spaces, Dashboards, then Goals ([What is the new navigation in Jira?](https://support.atlassian.com/navigation/docs/what-is-the-new-navigation-in-jira/)).
- Asana's 2023 sidebar opens with Home, My Tasks and Inbox, then Insights, Starred, Projects and Teams ([Navigating Asana](https://help.asana.com/s/article/navigating-asana), snippet only).
- Shortcut makes My Work the personal home, opened from the sidebar ([My Work](https://www.shortcut.com/help/views/my-work)).

### 2. Strategy and progress sit in their own group, apart from execution `[moderate]`

- Asana moved Reporting, Portfolios and Goals into an Insights section in 2023, and in 2025 split navigation into modes with a separate Strategy or Plan group ([sidebar redesign guide](https://forum.asana.com/t/ultimate-guide-to-the-new-sidebar-redesign-get-your-team-prepared/356082), community; [new navigation](https://forum.asana.com/t/asanas-new-navigation-experience/1104749), Asana staff).
- Linear keeps projects and initiatives under Workspace, apart from personal and team issue lists ([Navigating Linear](https://linear.app/enablement/guide/navigating-linear)).
- Jira places Goals below Spaces and Dashboards ([new navigation](https://support.atlassian.com/navigation/docs/what-is-the-new-navigation-in-jira/)).
- Downgrade: users of Asana's 2025 mode split report scattered starred items and extra clicks, so a hard wall between groups has a cost (forum, secondary).

### 3. Progress is a roll-up of the work beneath, shown as a bar; health is a separate human judgement `[moderate]`

- Linear measures project progress in estimate points, or one point per issue without estimates, with scope, started and completed lines; removing or cancelling issues lowers scope ([Project graph](https://linear.app/docs/project-graph)).
- Jira Plans rolls up by count (direct children only, as To do, In progress, Done bands) or by estimate (all levels) ([count](https://support.atlassian.com/jira-software-cloud/docs/track-progress-using-issue-count-in-advanced-roadmaps/), [estimates](https://support.atlassian.com/jira-software-cloud/docs/track-progress-using-estimates-in-advanced-roadmaps)).
- Asana goals roll up weighted progress from sub-goals, projects or tasks ([goal weights](https://forum.asana.com/t/effectively-assign-and-manage-goal-weights-to-measure-progress-more-accurately/881007), Asana staff).
- Health (on track, at risk, off track) is posted by a person in Linear, Asana and Shortcut, not computed; Linear says it tried computing progress from issue statistics and found it needed the team's input ([How we built project updates](https://linear.app/blog/how-we-built-project-updates), 2022, possibly stale).

### 4. Hierarchy lives in grouped lists and expandable tables, not in the rail `[moderate]`

- No surveyed product draws the initiative-to-issue tree in its sidebar. Linear groups and sub-groups views as swim lanes ([Display options](https://linear.app/docs/display-options)).
- GitHub Projects' table gained a "Show hierarchy" toggle that expands and collapses up to 8 levels, keeping group, sort and filter (public preview 2026-01-13) ([parent and sub-issue fields](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields)).
- Jira Plans and GitHub both leak filters through hierarchy: a parent that matches keeps children that do not, and users find it confusing ([Jira thread](https://community.atlassian.com/forums/Jira-questions/Howto-hide-quot-Done-quot-issues-from-a-plan/qaq-p/3015185), [GitHub discussion](https://github.com/orgs/community/discussions/184225)).

### 5. Done work is hidden by default in work views and opened on request `[moderate]`

- Linear's Active view excludes Backlog, Completed and Canceled; project views offer "completed in the last week, month or year", all, or none; sorting by status puts completed and canceled last ([Default team pages](https://linear.app/docs/default-team-pages), [Display options](https://linear.app/docs/display-options)).
- Shortcut's My Work hides completed stories by default ([My Work](https://www.shortcut.com/help/views/my-work)).
- Asana's My Tasks and Workload filter by completion status ([workload](https://help.asana.com/s/article/portfolio-workload-and-universal-workload), snippet).

### 6. Grouping and filtering by owner is a standard display option `[high]`

- Linear groups projects by lead and issues by assignee ([Display options](https://linear.app/docs/display-options)); Jira Plans groups by assignee with an Unassigned lane at the bottom ([Group issues](https://support.atlassian.com/jira-software-cloud/docs/group-issues-on-your-advanced-roadmaps-timeline/)); Shortcut filters epics and objectives by owner ([Filtering the Epics page](https://help.shortcut.com/hc/en-us/articles/209246966)); GitHub groups or slices by assignee.

### 7. A rail holds about six top-level destinations `[low]`

- Jira's new sidebar has about six groups; Shortcut's Views group has six entries; Linear's personal block has two items before shared sections. Downgrade: counted from docs, not measured use.

## Known unknowns

- **Known-unknown:** whether cancelled or withdrawn work counts toward done in any product's roll-up. Would be closed by: each vendor's roll-up formula; none of the fetched docs states it.
- **Known-unknown:** the live sidebar order in Asana's 2025 navigation, whose labels differ between sources. Would be closed by: a dated screenshot of the current app.
- **Unknowable:** which order serves *this* view's maintainers best. Why not: the products serve live, personalised, editable workspaces; this view is one read-only snapshot with no signed-in user, so only use of the shipped view can settle it.

## What this means for the intent view's rail `[inference]`

1. **Order the rail by job, not by data:** act now, report progress, tidy the graph, then browse. That mirrors finding 1's personal-first order and finding 2's separate strategy group, and it satisfies the view standard's "ranked by the job".
2. **Use labelled groups inside one rail, not modes.** Finding 2's downgrade argues against hiding destinations behind modes; small group labels keep every question one click away.
3. **The roadmap question measures, it does not judge.** Show delivered, in progress and not started over all work beneath, with withdrawn and archived apart (finding 3, and the owner's 2026-10-16 decision); never print "on track" or "at risk", because the records hold no health.
4. **Keep hierarchy in the list zone** as an expandable tree with expand-all and collapse-all (finding 4). When a filter is on, show non-matching ancestors dimmed and labelled as context, so the leak finding 4 names is explicit rather than confusing.
5. **Default work views to open work; offer Done explicitly** as All, Open, Done, with completed sorting last (finding 5).
6. **Owner is a filter and a grouping, with "No owner" last** (finding 6). With no signed-in user, there is no "My work"; an owner filter stands in for it.

Proposed rail, top to bottom:

| Group | Question | Job |
| --- | --- | --- |
| Work | What can I work on next? | Pick the next item (owner filter) |
| Work | What is broken? | Triage before starting |
| Progress | How far along is each capability? | Roadmap and progress for leadership |
| Progress | What is still open under a capability? | Drill into one capability's open work |
| Tidy | What has no parent? | Graph housekeeping |
| Browse | Browse all intents | Full tree: Show, Group, Owner |
