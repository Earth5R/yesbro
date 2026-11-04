---
title: Designing for the iPhone Duo, what Apple's foldable changes for UX and web design
slug: designing-for-iphone-duo-foldable-ux-web-design
date: 2026-10-27
dek: Apple's first foldable gives designers a squat outer screen, a 7.6 inch inner one and two new web APIs behind a flag. Here is what the first week of real use says about designing for it.
description: Designing for the iPhone Duo: viewport sizes, Safari's cramped outer screen, the Device Posture and Viewport Segments APIs, and what foldable UX means for designers.
---
Every new iPhone shape arrives with the same promise, that your app will just work. The iPhone Duo keeps that promise in the way a hotel keeps its promise of a sea view, technically and from one corner of the balcony. A week in, the reviews, the teardown and Apple's own developer notes give designers a clear picture of what actually changes.

## Two screens, one very wide passport

The basic geometry first. In its [iPhone Duo review](https://9to5mac.com/2026/10/21/iphone-duo-review/), 9to5Mac describes a 5.4 inch outer display and a 7.6 inch inner one, both with a 1.4:1 aspect ratio. Apple says the outer screen has 90% of the screen area of the iPhone 18 Pro, but the shape is shorter and wider. The reviewer's best description was to grab your passport and imagine it runs iOS.

That shape matters more than the diagonal. Wider means more horizontal room and far less vertical room than any phone your layouts were tested on. The same review says the device is a delight one handed for a right handed person, and 9to5Mac later [reported](https://9to5mac.com/2026/10/23/iphone-duo-has-hidden-trick-that-solves-a-common-complaint/) that left handed users found Control Center hard to reach with the usual top right swipe. The fix, found by users rather than announced, is tapping the new status icon, which drifts further down the screen when a Live Activity runs. Reachability, it turns out, still has opinions.

## Safari moved its controls, and your header lost

The design problem most reviewers flagged is in Safari. On the outer display, iOS moves the browser controls to the side to give content more vertical space. 9to5Mac [noted](https://9to5mac.com/2026/10/23/apple-exploring-fix-for-safaris-cramped-layout-on-the-iphone-duos-outer-display/) that those right aligned controls eat into the usable width, leaving websites an unusually narrow area.

Apple has said so itself. In the [WebKit post on Safari 27.1](https://webkit.org/blog/18486/webkit-features-for-safari-27-1/), Jen Simmons writes that websites cannot yet extend behind those controls. Apple could use the viewport meta tag with viewport-fit="cover", but its research found a lot of sites fail to inset all four edges correctly. So it is looking for something more foolproof and has asked developers for ideas. That is a polite way of saying it has seen your CSS.

The same post gives numbers every designer should pin to the wall. Across all the poses, the Safari viewport ranges from 382 to 951 CSS pixels wide and from 368 to 902 tall. The inner screen in landscape can also show two windows side by side, each with a narrow portrait viewport. If your breakpoints jump straight from phone to tablet, the Duo will find the gap.

## Posture is now a design input

The genuinely new part is the fold itself. Safari 27.1 ships a preview of the Device Posture API and the Viewport Segments API behind feature flags. The first tells a page whether the screen is partially folded, in a book or laptop pose. The second describes the segments on either side of the fold, so a layout can put a map on one half and the list on the other. Apple already uses the idea itself: hold the phone like a book while reading a PDF and Safari shows two pages side by side.

Behind a flag means the shape of these APIs can still change, which WebKit says plainly. It also means this is the cheapest moment to have an opinion. Designers can test without the hardware, since Xcode 27.1 includes a simulator for the device.

## The hinge is a UX problem too

Hardware still leaks into interaction design. iFixit's teardown, [summarised by 9to5Mac](https://9to5mac.com/2026/10/25/ifixit-tears-down-iphone-duo-finds-possible-causes-of-early-screen-failures/), gave the Duo a provisional repairability score of 5 out of 10, the highest it has given a foldable. It also explored possible causes of early inner screen failures that owners reported after hearing a crunch while folding. iFixit did not establish the cause. For designers, the lesson is modest and practical. Gestures that invite pressing near the fold, or constant opening and closing, are not free.

## What to do this week

Test layouts at 382 pixels wide and 368 tall, not just at your usual phone sizes. Check that sticky headers and side controls do not collide. Treat folded and unfolded as two contexts with their own jobs, not one screen stretched. And watch real people use the thing, because the best Control Center fix of the week came from users, not a spec sheet. If you want practice at that kind of observation, Earth5R's [FIELDWORK fellowship](https://earth5r.org/fieldwork/) is hands-on fieldwork with real people, real conversations and real user research. The fold is new. Watching people struggle with it is not.

