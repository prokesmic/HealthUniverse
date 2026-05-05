# Claude Brief: Stack Diary

Route:
- `/diary`

Files:
- `web/templates/diary.html`
- `web/static/style.css`

Goal:
- Make `/diary` feel like a thoughtful self-tracking companion, not a raw localStorage utility.

Current function to preserve:
- local-only diary data
- factor checkboxes
- outcome sliders
- save / export / clear
- trend summary
- days logged list

Design direction:
- warm, private, reflective
- should feel like a health journal
- trends area should feel helpful, not technical

What to improve:
- layout balance between logging and trend reading
- slider and checkbox polish
- make “stays on your device only” feel trustworthy
- trend presentation should feel more interpretable

Acceptance criteria:
- page is more inviting to use daily
- input controls feel intentional
- privacy promise is more visible
- current local-only behavior remains unchanged
