# Evidence Bot

Build a pixel-perfect, modern, responsive web application exactly matching the attached UI design for an AI Hallucination Mitigation System. Do not redesign the layout or change the overall visual style. Follow the reference image as closely as possible.

Tech Stack

React + Vite

TypeScript

Tailwind CSS

shadcn/ui

Lucide React icons

Framer Motion for subtle animations

React Router

Recharts (dashboard statistics)

React Flow (Knowledge Graph visualization)

Theme

Create a clean AI SaaS dashboard similar in quality to ChatGPT, Perplexity AI, and Notion AI.

Primary Color

#6C4CF5

Secondary

#8B7BFF

Accent

#ECE9FF

Background

#F8F9FD

Cards

White

Text

Primary: #1E1E2E

Secondary: #6B7280

Success

#22C55E

Warning

#F59E0B

Error

#EF4444

Border Radius

16px

Card Shadow

Soft shadow

Hover elevation

Typography

Font: Inter

Bold headings

Medium body

Small muted labels

Layout

Desktop Dashboard

Left Sidebar (Fixed)
Top Navbar
Scrollable Main Content

Sidebar Width
280px

Navbar Height
72px

Spacing
24px throughout

Everything should align exactly like the reference image.

Sidebar

Top
AI Hallucination Mitigation System

Navigation

Dashboard

New Verification

Ask a Question

Knowledge Graph

Sources

History

Uploads

Settings

About Us

Bottom Section

AI Accuracy, Built on Real Evidence

Dark Mode Toggle

Logout Button

Active page should have

Purple background

Rounded corners

Purple icon

Smooth hover animation

Navbar

Left

Hamburger Menu

Center

Global Search Bar

Placeholder

Search anything...

Shortcut hint

Ctrl + K

Right

Notification Icon

Profile Avatar

Username

Dropdown

Sticky navbar with blur effect.

Dashboard

Heading

Welcome back, Shivaleela! 👋

Subtitle

Verify claims, ask questions and get evidence-based answers.

Right side

Friendly AI robot illustration

Start New Verification Card

Large rounded card.

Title

Start New Verification

Subtitle

Type a claim/question or upload files to get accurate evidence-based answers.

Input

Large rounded input

Placeholder

Enter your claim or question here...

Below Input

Upload Files Button

Supported files

PDF

TXT

DOCX

CSV

Maximum size

20MB

Primary CTA

Verify / Ask

Purple filled button

Arrow icon

Statistics Cards

Four equal cards.

Card 1

Chat Icon

32

Total Verifications

Card 2

Green Check

18

Supported

Card 3

Red Alert

8

Refuted

Card 4

Orange Badge

6

Not Enough Info

Cards should animate upward slightly on hover.

Recent Verification Card

Table

Columns

Claim

Result

Date

Badges

Supported

Green

Refuted

Red

Not Enough Info

Orange

Top Right

View All

System Overview Card

Four connected steps

Retrieve Information

↓

Build Knowledge Graph

↓

Verify / Generate Answer

↓

Provide Result

Use simple icons connected with arrows.

New Verification Page

Two-column layout.

Left

Large textarea

Placeholder

Type your claim or question...

Character counter

Example chips

"The moon is made of cheese"

"Plants get energy from the sun"

"Earth is the center of the universe"

"Does drinking hot water burn fat?"

Right

Upload Card

Large drag-and-drop zone

Upload icon

Browse Files Button

Uploaded file card

Filename

File size

Remove button

Dropdown

Retrieval Source

Default

All Sources

Advanced Options accordion

Bottom

Large Verify / Ask button.

Ask a Question Page

ChatGPT-like interface.

Top

New Chat Button

User message bubble

Purple

Assistant response

White card

Include

Answer

Supporting explanation

Sources list

Button

View Sources

Bottom

Chat input

Send button

Typing animation

Auto scroll

Answer Details Page

Card 1

User Question

Card 2

Answer

Card 3

Result

Supported badge

Card 4

Confidence Score

Progress bar

Percentage

High label

Card 5

Supporting Evidence

Accordion list

Each item

Source Name

View Button

Expandable evidence

Share Button

Top Right

History Page

Search bar

Filter dropdown

Table

Columns

Type

Claim / Question

Result

Confidence

Date

Action

Status colors

Green

Orange

Red

Pagination

Bottom center

Uploads Page

Uploaded documents table

Columns

Filename

Type

Uploaded Date

Status

Size

Delete

Preview

Upload button

Drag and drop

Progress indicator

Knowledge Graph

Interactive graph

React Flow

Purple nodes

Curved edges

Zoom

Pan

Search node

Click node

Open entity details panel

Sources Page

Cards showing

Wikipedia

Research Papers

Uploaded Documents

Government Sources

Books

Each source should display

Title

Snippet

Relevance Score

Open Source button

Animations

Framer Motion

Fade in

Slide up

Card hover

Button hover

Smooth page transitions

Animated progress bars

Loading skeletons

Micro interactions everywhere

Responsiveness

Desktop

Laptop

Tablet

Mobile

Sidebar collapses

Cards stack

Tables become responsive

Maintain identical visual hierarchy.

Accessibility

Keyboard navigation

ARIA labels

Visible focus states

Proper contrast ratio

Semantic HTML

Important

The final UI must closely replicate the attached reference image in layout, spacing, typography, colors, shadows, component placement, and proportions.

Do not simplify, redesign, or replace the layout. Create reusable React components for every section and ensure the interface looks like a premium AI SaaS product ready for production.

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://insight-weave-849.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/542dba03-b0f2-4eb6-a7b5-e02538fedaff).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
