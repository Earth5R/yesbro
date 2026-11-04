---
title: Touchscreen MacBook Pro, what Apple's touch on Mac rules mean for UX and app design
slug: touchscreen-macbook-pro-designing-for-touch-on-mac
date: 2026-10-30
dek: Apple has put touch on the Mac without redesigning macOS for fingers. Its design guidance is a lesson in restraint, with a 36 point touch target, controls that grow only when touched, and a firm rule about hover.
description: Designing for the touchscreen MacBook Pro: Apple's 36 point touch target, expanding controls, hover rules and gestures, and what touch on Mac means for UX designers.
---
In 2010 Steve Jobs said touch surfaces "don't want to be vertical" and that after a while "your arm wants to fall off," as [Creative Bloq](https://www.creativebloq.com/news/apples-touchscreen-macbook-pro-makes-more-sense-than-you-might-think) helpfully reminded everyone this week. Apple has now shipped a touchscreen MacBook Pro anyway. The interesting part for designers is not that Apple changed its mind. It is how little of the Mac it changed to do it.

## What Apple launched

[Apple's announcement](https://www.apple.com/newsroom/2026/10/apple-unveils-groundbreaking-macbook-pro-with-proled-xdr-display/) introduces the MacBook Pro with PROLED XDR Display in 14 and 16 inch sizes, with touch on a Mac for the first time. Pre-orders opened on 28 October and availability begins on 6 November. Apple says many existing apps work with touch right away "because macOS automatically translates touches into clicks," and that the touch sensor is built into the display panel to reduce latency.

The gestures are the ones your thumb already knows. Swipe to scroll, pinch to zoom, drag slides between presentations, double-tap a window to fill the screen, flick to tile it.

## The design move is restraint

Back in 2016, [MacRumors recalls](https://www.macrumors.com/2026/10/29/macos-adapts-controls-touch-macbook-pro/), Phil Schiller argued that touch on a Mac would mean "totally redesigning the menu bar for fingers." Apple's answer is subtler. The menu bar looks the same, but a menu item expands under a fingertip. The red, yellow and green window buttons get bigger when touched, and then you tap. The Dock hides until you swipe up from the bottom.

Apple's developer tech talk, [Design for touch on Mac](https://developer.apple.com/videos/play/tech-talks/111456/), covers touch targets, hover and the expansion of controls like steppers, dials and sliders. A detailed write-up of the talks by [Blake Crosley](https://blakecrosley.com/blog/touch-on-mac-for-developers) quotes the rules worth pinning above your desk. The touch target on macOS is 36 points, which the talk says gives "the same physical size on display as iOS's 44 points." That target is invisible. Controls do not change size, so layouts do not change. For custom controls, the advice is to enlarge the touch area around a control rather than the control itself.

The closing rules are almost severe. "Avoid redesigning your app just to support touch." An app on a touch Mac "should have no visual distinction" from the same app on a Mac without touch. "Keep keyboard and mouse as a primary input."

## Where the hand goes

The most useful guidance is about anatomy. According to the same write-up, the talk notes that the edges of the display are easy to reach by holding the side of the screen, so the left and right of a window suit dense UI such as inspectors and sidebars. The centre is "best used for coarse, imprecise and big gestures."

Custom gestures come with conditions. They should work with touch and trackpad, not touch alone, and the action should also exist elsewhere in the UI, for example in a menu. Hover gets the same treatment. Only the most important hover actions should appear on touch, and actions that appear on hover should be duplicated elsewhere in the interface.

## Our view

This is a good brief for designers who have spent a decade making tablet versions of desktop apps. Apple is saying touch is an extra input, not a new platform. That makes the hard work invisible. Hit areas, hover dependencies and gestures without a menu fallback are exactly the things nobody notices until a finger fails on them.

Apple says it is not finished. [9to5Mac reports](https://9to5mac.com/2026/10/29/apple-says-its-only-getting-started-updating-macos-for-touchscreens/) that an Apple employee told the press the company is "only getting started" optimising macOS for touch.

## What to check this week

Audit every hover-only action and give it a second home. Measure custom hit areas against 36 points. Move precision controls toward the edges of the window. Then watch someone use it, because guidance tells you where the hand should go and only observation tells you where it does. Earth5R's [FIELDWORK fellowship](https://earth5r.org/fieldwork/) trains exactly that habit, with hands-on user research and real conversations with real people. Steve Jobs worried about tired arms. Your users will tell you whether he was right.
