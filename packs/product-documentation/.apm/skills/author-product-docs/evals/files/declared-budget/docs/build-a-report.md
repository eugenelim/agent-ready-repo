# Build a report

Build a report from your project data so you can send it to your team.

This page walks through every setting that the report file accepts, because teams often ask what each one does, and it explains the order in which the settings are read. The order matters when two settings conflict: a later key wins over an earlier one, and a key set in a section wins over the same key set at the top of the file. Teams that share a file should agree who owns each section.

1. Step 1: Open the project folder and find the file named `report.cfg`.
2. Step 2: Read the comments at the top of the file so you know which section controls the layout.
3. Step 3: Set the `title` key to the name your readers will recognize.
4. Step 4: Set the `author` key to your team name, not to a person.
5. Step 5: Choose a date style: `iso` writes 2031-04-02, `long` writes 2 April 2031.
6. Step 6: Set `date_style` to your choice and save the file.
7. Step 7: Choose whether the report includes a table of contents by setting `toc` to `yes` or `no`.
8. Step 8: If you chose `yes`, set `toc_depth` to the number of heading levels you want listed.
9. Step 9: Pick a page size: `a4` or `letter`, and set `page_size`.
10. Step 10: Pick margins in millimetres and set `margin_mm`; 20 works for most teams.
11. Step 11: Choose a font family from the list in the file comments and set `font`.
12. Step 12: Set `font_size` between 9 and 14; 11 is the usual choice for printed copies.
13. Step 13: Decide whether to print page numbers and set `page_numbers` to `yes` or `no`.
14. Step 14: Decide whether to add a footer line and set `footer` to the text you want, or leave it empty.
15. Step 15: Save the file and close it so no other program holds it open.
16. Step 16: Run the build from the project folder using your normal build button or command.
17. Step 17: Wait for the build to finish; small reports take a few seconds and large ones can take a minute.
18. Step 18: Open the `out` folder and look for the file named after your title.
19. Step 19: Open the file and check the title page, the table of contents, and the first two pages.
20. Step 20: If anything looks wrong, return to the file, change one key, and build again.

## Settings you may want later

Teams sometimes ask for a cover image, a watermark, a second language, a custom header, or a different numbering style. Each has a key in the file, and each is described in the comments next to the key. Read those comments before you add a key, and keep a copy of the file before you change it, because the build does not warn you about unknown keys. If you share the file with another team, tell them which keys you changed and why, so that a later build does not undo the change by accident.
