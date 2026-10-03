# Requirements and implementation mapping

## Available sources

- User's explicit feature request in this chat.
- Retrieved Week 4 Help conversation: minimum registration/login, car viewing, booking; documented Python/Django/SQLite/Templates/Admin stack; mock payments and Django email.
- Repository snapshot at 3b03ff3aef6f995dec02ebeeb3d6589ad9cbacc5, retrieved via read-only GitHub connector.
- Uploaded assignment and weekly report binaries were not available. No claim is made that every unseen requirement has been verified.

| Requirement | Implementation | Verification |
| --- | --- | --- |
| Registration/login/logout | Django auth, password validators/hashing, POST logout | Registration, duplicate, mismatch, login/logout tests |
| Duplicate accounts | Normalized registration, case-insensitive checks, unique email registry | Duplicate email/username test |
| Customer profile | Optional phone/address, name/email from registration | Profile persistence test |
| Car catalog/details | Existing Category/Car models, category daily rates, responsive templates | Catalog/detail tests |
| Category/transmission/availability filters | Validated query form and date conflict exclusion | Filter/invalid-query tests |
| Pickup/return validation | Form/model validation and DB return-after-pickup constraint | Past/equal/reversed date tests |
| Conflict prevention | Shared booking validation, SQLite IMMEDIATE atomic saves | Overlap/adjacency tests and two-thread file DB check |
| Price calculation | Decimal, duration × saved category rate | Forged-price and rate-retention tests |
| Mock checkout/confirmation | Simulated approve/decline, explicit consent, receipt view | Payment decline/approve/repeat/consent tests |
| Notifications | Console emails after committed payment/change/cancellation | Confirmation email test |
| Customer booking history | Owner-scoped list/detail | Privacy tests |
| Cancellation/modification | Before pickup day, mock refunds/re-checkout, conflict revalidation | Cancellation, modification, pickup-day tests |
| Staff management | Django Admin categories/cars/bookings/profiles/users | Access/list and admin form validation tests |
| Sample data | Idempotent seed_data command | Seed idempotency test |
| Local Windows runtime | Pinned Django, committed migration files, direct venv executable instructions | Fresh migrate/check/test performed locally |

## Changes from repository

Existing anonymous booking creation was replaced by authenticated ownership.
Added account/profile flows, booking lifecycle/payment/price fields, details/history, owner authorization, console email, responsive styles, sample fleet, and tests.
Existing 0001/0002 migrations remain; 0003 adds new models/fields/constraints.
Legacy anonymous bookings, if present in an old database, remain admin-visible with no customer owner. This package is intended for a new local database. It does not automatically claim old bookings or backfill their rates/payments.

## Policies chosen where original materials were unavailable

Return-exclusive dates; category rate snapshot; modification of dates only; customer changes before pickup day; unpaid bookings reserve dates until cancellation; no actual payment processor; console email; protected booking history. Review these choices against the original reports before submitting.

## Design

Browser → Django views/forms → shared Booking validation/save → SQLite.
Django Templates render customer pages; Django Admin provides staff CRUD.
SQLite IMMEDIATE transactions acquire a write lock before checking conflicts, so concurrent writers serialize.
Direct SQL/bulk updates can bypass model validation and must not be used for booking changes.
Use the provided views or Django Admin.
