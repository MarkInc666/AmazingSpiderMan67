# Villain and wizard opening ball saves — November 2, 2026

## Implemented policy

- Every one of the 55 villain modes receives a shared **20-second opening save**.
- Collected Safety Net makes that opening save **30 seconds**.
- All 12 wizard opening multiball saves are now **30 seconds**.
- Wizard add-a-ball durations and Final Showdown final-shot retry rules remain unchanged.
- Existing later-phase saves, objective-protection helpers, and native villain
  multiball windows remain separate. Existing More Time windows are preserved.

This implements the decision made after `ASM67_ball_save_audit_2026-11-02.md`.
That audit remains the historical pre-change inventory.

## Install

Apply this changed-files-only ZIP over the project **after the earlier patches**,
then restart MPF. Base checkpoint: `ASM67_2026_11_01_11pm(1).zip` plus the
skill-shot/lane-carryover, chapter settling, Mystery eligibility, opening-ball
protection, and fourth-lane-outlane-save patches from this conversation.

The included config/player_vars.yaml and config/config.yaml retain earlier
lane-carryover variables and the 25-second normal-ball opening save.

## When the timer starts

The shared helper registers the save for the actual gameplay-mode-started edge,
after chapter/villain selection and the bookend intro. If a saucer, VUK or
plunger is occupied at that point, protection is enabled but its countdown waits
for the first release from those switches. If none is occupied, counting starts
immediately. Only the first release starts the timer. Subsequent saved-ball
relaunches and later captures/releases do not renew it. Mode stop disables it;
ball end and tilt also disable the global device.

The new device saves unlimited drains during its window and auto-launches
replacements. It uses a 3-second hurry-up and a 2-second grace period; those
are additional device settings beyond the 20/30-second configured active time.

Shoot Again, ball-save count tracking, saved-ball messages and plunger relaunch
flags include the new device. This also preserves earned outlane saves while
the opening timed protection is enabled.

## Integration details

- `CaseFileMixin.reset_active_mode_summary()` registers the shared opening-save
  lifecycle for all 55 villains. The duration snapshot is stored in the new
  player variable `villain_opening_save_seconds`.
- Thirty former startup-only requests for the shared 20-second Case File save
  were removed because the new 30-second Safety Net opening save replaces them.
  Later requests for that existing device are preserved.
- All 55 Safety Net helper descriptions include 30-second opening protection.
  Later shared Case File saves are described as 20 seconds where applicable.
- Doctor Cool, Enforcers and Desperado now put CaseFileMixin before Mode in
  their inheritance lists, allowing their existing super().mode_stop() calls
  to reach the shared cleanup, consistently with the other villains.
- Each wizard's native multiball shoot_again setting changes from 20s to 30s.
  No wizard objective, ball count or add-a-ball setting changes.

## Validation

**660 actual villain-startup/release/stop cases passed** using stubbed MPF
services: all 55 modes, Safety Net absent/present, and six startup states
(no held ball, each of three saucers, VUK, or plunger).

Checks confirm duration selection, delayed countdown for initial holds,
immediate countdown when no starting ball is held, one timer start per attempt,
no renewal on later release, and disabling protection on mode stop.

All 12 wizard opening settings and unchanged wizard add-a-ball settings were
verified. The shared save device, Shoot Again registration, enable/disable
save-count mappings and saved-ball relaunch UI mapping were checked.
Existing skill-shot checks (72 scenarios), Mystery eligibility checks (260
checks plus fallback), and chapter-select settling checks still pass.
All modified Python and YAML parse successfully.

These are software and configuration checks. MPF/GMC event integration and
physical-machine timing remain unconfirmed.

## Machine checks

1. Start a villain without Safety Net: confirm 20-second opening protection.
2. Repeat with Safety Net: confirm 30 seconds and the corrected helper text.
3. Wait through an intro and an initial held-ball sequence: the countdown must
   start on release, rather than expiring while the ball is parked.
4. Drain during protection: confirm one replacement and Shoot Again feedback.
5. Confirm a replacement plunge does not restart the opening timer.
6. Start a wizard and confirm 30-second multiball opening protection.
7. Confirm mode stop/tilt removes the new save, and later-phase/helper saves
   still occur at their original triggers.
