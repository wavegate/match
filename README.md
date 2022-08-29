# Residency Mtach

This is an application intended for medical residency applicants to have a more organized format to share interview season experiences.

## Table of contents

- [Overview](#overview)
  - [The challenge](#the-challenge)
  - [Screenshot](#screenshot)
  - [Links](#links)
- [My process](#my-process)
  - [Built with](#built-with)
  - [What I learned](#what-i-learned)
  - [Continued development](#continued-development)
- [Author](#author)

## Overview

### Application functionality

Users should be able to:

- Create an account and log in
- Peruse general information about each medical residency
- Submit when they received an interview invite from a residency and the information associated with those invites (dates available, dates full, form of contact, etc.)
- View interview impressions from previous years and add interview impressions for the current year
- Ask questions and receive replies in each specialty

### Screenshot

![](./screenshot.jpg)

### Links

- Note that this is the staging app and not the production app; the production app is currently down
- Live Site URL: [https://match0912-staging.herokuapp.com](https://match0912-staging.herokuapp.com)

## My process

- I built this while I was still in medical school at the advice of a friend. There is a large need for an app like this but I didn't quite finish it because I got stuck on the data processing part. The time-consuming part was processing previous years' data (which were just spreadsheets where people wrote all sorts of stuff), and it was difficult to parse so much information.
- I used Paper UI from creative-tim, which saved me from having to build the UI from scratch.
- I used Flask and followed a tutorial. I struggled a lot with trying to figure out how to properly populate the database with data from residencies, ultimately resorting to creating a URL endpoint that would run and populate the database with an uploaded Excel sheet with the data that I wanted uploaded. It was difficult to change the data structure while I was testing things so I often had to reset the database. For some reason, making migrations for the database was just very error-prone. Since then, I've had a much better time with Django.

### Built with

- Flask
- PostgresQL
- Heroku
- Paper UI (creative tim)

## Author

- Website - [wavegate](https://github.com/wavegate)
