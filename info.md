1. `python3 -m venv venv`: Creates a virtual environment
2. `pip install -r requirements.txt`: Installs project dependencies 
3. `python3 app.py`: Runs the Flask application !
4. & ".\venv\Scripts\python.exe" app.py





1. `prompt to change the change/add footer `

Update `@tempalets/base.html` footer:

- Add clickable Terms and Conditions and Privacy Policy links.
- Add `Crafted with ♥ by Manish | © 2026 All Rights Reserved`.
- Make Manish clickable, but prevent navigation or any action on click.
- Keep links as placeholders without navigation, popups, or page reloads.
- Match the existing design and ensure mobile responsiveness.

Modify only the footer and preserve all existing functionality.


### add terms and conditions page and route(contetn) and for privacy also

Update my Flask expense tracker project:

1. Add Privacy Policy and Terms & Conditions pages with appropriate content.
2. Make both footer links clickable and navigate to their respective pages.
3. Add routes for both pages in `app.py`.
4. Create `privacy_policy.html` and `terms_and_conditions.html` inside `templates/`, extending `base.html`.
5. Match the existing website design and ensure mobile responsiveness.

Modify only the necessary files and preserve existing functionality.


git commit -m"landing : added terms and conditions page and privace page and routes"


3. re-designing here section of the landing page
  [inserted image]

  Replace only the existing hero section with the attached reference design. Recreate its headline, green badge, description, two CTA buttons, and expense dashboard preview. Match the colors, typography, spacing, and responsive layout. Preserve existing functionality and do not modify the header, footer, or other sections.


  git commit message : feat: redesign hero section with expense dashboard preview