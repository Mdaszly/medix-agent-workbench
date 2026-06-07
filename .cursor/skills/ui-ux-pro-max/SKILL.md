---
name: ui-ux-pro-max
description: >-
  Applies UI/UX design intelligence for web and mobile frontends: styles, color palettes,
  typography, accessibility, responsive layout, and component patterns. Use when building
  or refactoring pages, components, layouts, design systems, animations, or reviewing
  frontend UI for accessibility and visual consistency (React, Vue, Tailwind, shadcn, etc.).
---

# UI/UX Pro Max - Design Intelligence

Comprehensive design guide for web and mobile applications. Contains 67 styles, 161 color palettes, 57 font pairings, 161 product types with reasoning rules, 99 UX guidelines, and 25 chart types across 15 technology stacks.

## When to Apply

This Skill should be used when the task involves **UI structure, visual design decisions, interaction patterns, or user experience quality control**.

### Must Use
- Designing new pages (Landing Page, Dashboard, Admin, SaaS, Mobile App)
- Creating or refactoring UI components (buttons, modals, forms, tables, charts)
- Choosing color schemes, typography systems, spacing standards, or layout systems
- Reviewing UI code for user experience, accessibility, or visual consistency
- Implementing navigation structures, animations, or responsive behavior
- Making product-level design decisions (style, information hierarchy, brand expression)

### Skip
- Pure backend logic development
- Only involving API or database design
- Performance optimization unrelated to the interface
- Infrastructure or DevOps work
- Non-visual scripts or automation tasks

## Priority Rule Categories

| Priority | Category | Impact | Key Checks |
|---|---|---|---|
| 1 | Accessibility | CRITICAL | Contrast 4.5:1, Alt text, Keyboard nav, Aria-labels |
| 2 | Touch & Interaction | CRITICAL | Min 44×44px touch targets, 8px+ spacing, Loading feedback |
| 3 | Performance | HIGH | WebP/AVIF, Lazy loading, Reduced motion support |
| 4 | Layout & Responsive | HIGH | Viewport meta, Readable font size, No horizontal scroll |
| 5 | Typography & Color | MEDIUM | Line height 1.5-1.75, 65-75 chars per line |
| 6 | Animation | MEDIUM | 150-300ms duration, Use transform/opacity |

## Core UX Guidelines

### Accessibility
- color-contrast: Minimum 4.5:1 ratio for normal text
- focus-states: Visible focus rings on interactive elements
- alt-text: Descriptive alt text for meaningful images
- aria-labels: aria-label for icon-only buttons
- keyboard-nav: Tab order matches visual order

### Touch & Interaction
- touch-target-size: Minimum 44x44px touch targets
- hover-vs-tap: Use click/tap for primary interactions
- loading-buttons: Disable button during async operations
- cursor-pointer: Add cursor-pointer to clickable elements

### Performance
- image-optimization: Use WebP, srcset, lazy loading
- reduced-motion: Check prefers-reduced-motion
- content-jumping: Reserve space for async content

### Layout & Responsive
- viewport-meta: width=device-width initial-scale=1
- readable-font-size: Minimum 16px body text on mobile
- z-index-management: Define z-index scale (10, 20, 30, 50)

### Typography & Color
- line-height: Use 1.5-1.75 for body text
- line-length: Limit to 65-75 characters per line

### Animation
- duration-timing: Use 150-300ms for micro-interactions
- transform-performance: Use transform/opacity, not width/height

## Popular UI Styles

| Style | Best For | Key Features |
|---|---|---|
| Minimalism | Enterprise apps, dashboards | Clean, whitespace, readability |
| Glassmorphism | Modern SaaS, financial | Translucent cards, backdrop blur |
| Neumorphism | Health/wellness apps | Soft shadows, subtle depth |
| Claymorphism | Educational apps | Soft, rounded, playful |
| Dark Mode | Night-mode apps | OLED-friendly, reduced eye strain |
| Bento Box Grid | Dashboards, portfolios | Modular layout, information hierarchy |
| AI-Native UI | AI products, chatbots | Clean, conversational, assistant-style |

## Color Palettes by Industry

| Industry | Primary | Secondary | Mood |
|---|---|---|---|
| Healthcare | Teal/Cyan | Soft Green | Trust, calm, professional |
| Fintech | Navy Blue | Accent Green | Security, reliability |
| SaaS | Blue/Indigo | Vibrant accent | Modern, tech-forward |
| E-commerce | Warm Orange | Complementary | Energetic, conversion-focused |
| Beauty/Spa | Soft Pink | Sage Green | Calming, premium, elegant |
| Education | Warm Red | Gold accent | Engaging, trustworthy |

## Font Pairings

| Pairing | Mood | Best For |
|---|---|---|
| Inter + Roboto Slab | Modern professional | Enterprise, SaaS |
| Montserrat + Open Sans | Clean versatile | General purpose |
| Poppins + Lato | Friendly approachable | Consumer apps |
| Playfair Display + Roboto | Elegant sophisticated | Luxury, editorial |
| Nunito + Nunito Sans | Playful modern | Lifestyle, creative |

## Landing Page Patterns

1. **Hero-Centric**: Strong visual identity, CTA above fold
2. **Conversion-Optimized**: Lead generation, sales pages
3. **Feature-Rich**: Complex products, detailed showcase
4. **Social Proof-Focused**: Services, testimonials, trust elements
5. **Storytelling-Driven**: Brands, agencies, nonprofits

## Responsive Breakpoints

- Mobile: 375px
- Tablet: 768px
- Desktop: 1024px
- Large Desktop: 1440px

## Pre-Delivery Checklist

- [ ] No emojis as icons (use SVG: Heroicons/Lucide)
- [ ] cursor-pointer on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard nav
- [ ] prefers-reduced-motion respected
- [ ] Responsive at all breakpoints

## Supported Stacks

React, Next.js, Vue, Nuxt.js, Nuxt UI, Svelte, SwiftUI, React Native, Flutter, HTML+Tailwind, shadcn/ui, Jetpack Compose, Angular, Laravel

## Usage

When user requests UI/UX work (design, build, create, implement, review, fix, improve), analyze requirements and apply appropriate guidelines from this skill.
