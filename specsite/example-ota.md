# OTA firmware updater

Specification of the over-the-air firmware updater for a battery-powered
sensor node. Every typed block cites the paragraph of the brief it came
from as `brief §N`. Prose between blocks explains modelling choices; the
blocks are the model.

## Structure

The node carries the updater. The server is outside the node and is only
reached over one boundary.

```{component} sensor node
:id: COMP-NODE
:kind: system
:source: brief §1
The battery-powered sensor node whose firmware is updated over the air.
```

```{component} OTA updater
:id: COMP-UPDATER
:kind: subsystem
:source: brief §1
:part_of: COMP-NODE
:satisfies: REQ-BATTERY-RESERVE
Runs the update steps in order and reports the device state to the server
after every step. It pauses its own download when battery is low, which is
how the node keeps its battery reserve.
```

```{component} update server
:id: COMP-SERVER
:kind: external
:source: brief §1
Hosts firmware images and receives the device's state reports.
```

```{interface} server link
:id: IF-SERVER
:kind: boundary
:source: brief §1
:part_of: COMP-UPDATER
Boundary between the updater and the update server: update check, image
download, state reports.
```

### Artifacts

The two firmware banks are modelled by role, not by slot number: at any
moment one bank is active and one is inactive, and the roles swap when a
new bank is marked active.

```{artifact} staging slot
:id: ART-STAGING-SLOT
:kind: storage
:source: brief §5
Holds the downloaded image in chunks until it is verified and copied to a
bank.
```

```{artifact} active firmware bank
:id: ART-BANK-ACTIVE
:kind: storage
:source: brief §5
The bank the device currently boots from. It is never written during an
update.
```

```{artifact} inactive firmware bank
:id: ART-BANK-INACTIVE
:kind: storage
:source: brief §5
The bank that receives the new image. It becomes the active bank when the
update is confirmed.
```

```{artifact} update record
:id: ART-UPDATE-RECORD
:kind: record
:source: brief §5
Persistent record of the current update: attempt counter, outcome of every
attempt, bank switches, and a paused download if any.
```

```{artifact} health report
:id: ART-HEALTH-REPORT
:kind: message
:source: brief §5
Report produced by the new firmware after reboot stating whether it runs
healthy.
```

## Behaviour: the update sequence

The seven steps of brief §1 are actions. The three checks of brief §2 are
decisions; the pass path is `flows_to`, the fail path is `fails_to`. The
"confirm healthy" step is split into an action that collects the health
report and a decision that judges it, so the 60 s bound sits on the
decision.

```{action} check for update
:id: ACT-CHECK
:kind: step
:source: brief §1
:flows_to: DEC-UPDATE-AVAILABLE
:uses: COMP-SERVER
:reads: ART-UPDATE-RECORD
Asks the server whether an image newer than the running firmware exists.
Reads the update record first so that a paused download (brief §3) is
resumed instead of restarted.
```

```{decision} update available?
:id: DEC-UPDATE-AVAILABLE
:kind: gate
:source: brief §2
:condition: server reports an image newer than the running firmware, or a paused download exists in the update record
:flows_to: ACT-DOWNLOAD
:fails_to: ACT-SLEEP
If no update is available the updater goes back to sleep.
```

```{action} download image
:id: ACT-DOWNLOAD
:kind: step
:source: brief §1
:part_of: LOOP-DOWNLOAD-RETRY
:flows_to: DEC-IMAGE-VALID
:uses: COMP-SERVER
:writes: ART-STAGING-SLOT, ART-UPDATE-RECORD
:satisfies: REQ-RETRY-LIMIT, REQ-UPDATE-RECORD
Fetches the image in chunks into the staging slot. Each new attempt
increments the attempt counter in the update record; a resumed download
keeps the counter.
```

```{decision} checksum and signature match?
:id: DEC-IMAGE-VALID
:kind: gate
:source: brief §2
:part_of: LOOP-DOWNLOAD-RETRY
:condition: checksum of the staged image equals the expected checksum and the signature verifies against the device's trusted key
:flows_to: ACT-WRITE-BANK
:fails_to: LOOP-DOWNLOAD-RETRY
A mismatch sends control to the retry loop, which decides whether another
download attempt is allowed.
```

```{action} write image to inactive bank
:id: ACT-WRITE-BANK
:kind: step
:source: brief §1
:flows_to: ACT-REBOOT
:reads: ART-STAGING-SLOT
:writes: ART-BANK-INACTIVE
:satisfies: REQ-NO-ACTIVE-WRITE
Copies the verified image from the staging slot into the inactive bank.
The active bank is never a write target.
```

```{action} reboot into new bank
:id: ACT-REBOOT
:kind: step
:source: brief §1
:flows_to: ACT-CONFIRM-HEALTH
:reads: ART-BANK-INACTIVE
:writes: ART-UPDATE-RECORD
Boots the device from the newly written bank. The boot is logged in the
update record.
```

```{action} collect health report
:id: ACT-CONFIRM-HEALTH
:kind: step
:source: brief §1
:flows_to: DEC-HEALTHY
:reads: ART-HEALTH-REPORT
Waits for the new firmware to produce its health report.
```

```{decision} healthy within 60 s?
:id: DEC-HEALTHY
:kind: gate
:source: brief §2
:condition: a health report with status healthy arrives within 60 s of reboot
:limit: 60 s
:flows_to: ACT-ACTIVATE
:fails_to: ACT-ROLLBACK
No healthy report within 60 s of reboot counts as a fail.
```

```{action} mark new bank active
:id: ACT-ACTIVATE
:kind: final
:source: brief §1
:result: update complete; the new bank is active and the previous bank becomes inactive
:writes: ART-UPDATE-RECORD
:satisfies: REQ-UPDATE-RECORD
Swaps the bank roles and records the bank switch and the successful
outcome in the update record.
```

```{action} roll back to previous bank
:id: ACT-ROLLBACK
:kind: final
:source: brief §2
:result: update marked failed; device runs the previous bank
:reads: ART-BANK-ACTIVE
:writes: ART-UPDATE-RECORD
:satisfies: REQ-AUTO-ROLLBACK, REQ-UPDATE-RECORD
Reboots into the previous (still active) bank and marks the update as
failed in the update record.
```

```{action} sleep until next check
:id: ACT-SLEEP
:kind: final
:source: brief §2
:result: device sleeps; the next scheduled check starts a new run
Reached when no update is available or when the download loop abandons
the update.
```

### Rules

```{rule} report state after every step
:id: RULE-REPORT-STATE
:kind: reporting
:source: brief §1
:applies_to: ACT-CHECK, ACT-DOWNLOAD, ACT-WRITE-BANK, ACT-REBOOT, ACT-CONFIRM-HEALTH, ACT-ACTIVATE, ACT-ROLLBACK, ACT-SLEEP
After every step the device reports its current state to the server over
the server link.
```

## The download retry loop

The loop is bounded by the attempt counter in the update record and
measures progress in verified chunks. Its states show the pause on low
battery and the two ways out: a verified image or an abandoned update.

```{loop} download retry
:id: LOOP-DOWNLOAD-RETRY
:kind: retry
:source: brief §3
:limit: 3 attempts per update, counted in the persistent update record
:measure: number of verified chunks
:reenters: ACT-DOWNLOAD
:result: after 3 failed attempts the update is abandoned and the device sleeps until the next check
Entered when checksum or signature verification fails. A pause on low
battery does not consume an attempt; the counter is kept across the pause.
```

### States

```{state} downloading
:id: STATE-DOWNLOADING
:kind: running
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:flows_to: TR-CHUNKS-DONE, TR-BATTERY-LOW
Chunks are being fetched into the staging slot.
```

```{state} verifying
:id: STATE-VERIFYING
:kind: running
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:flows_to: TR-VERIFY-OK, TR-VERIFY-RETRY, TR-VERIFY-EXHAUSTED
Checksum and signature of the staged image are being checked.
```

```{state} paused on low battery
:id: STATE-PAUSED
:kind: paused
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:flows_to: TR-RESUME
The download is suspended. Attempt counter and verified chunks are kept
in the update record.
```

```{state} verified
:id: STATE-VERIFIED
:kind: final
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:result: image accepted; control continues with writing the inactive bank
```

```{state} abandoned
:id: STATE-ABANDONED
:kind: final
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:result: update abandoned; device sleeps until the next check
```

### Transitions

```{transition} chunks done: all chunks received
:id: TR-CHUNKS-DONE
:kind: guard
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:condition: every chunk of the image has been received into the staging slot
:to_state: STATE-VERIFYING
```

```{transition} verified: checksum and signature match
:id: TR-VERIFY-OK
:kind: guard
:source: brief §2
:part_of: LOOP-DOWNLOAD-RETRY
:condition: checksum matches and signature verifies
:to_state: STATE-VERIFIED
```

```{transition} mismatch: attempts < 3
:id: TR-VERIFY-RETRY
:kind: guard
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:condition: checksum or signature does not match and the attempt counter in the update record is below 3
:to_state: STATE-DOWNLOADING
```

```{transition} mismatch: attempts = 3
:id: TR-VERIFY-EXHAUSTED
:kind: guard
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:condition: checksum or signature does not match and the attempt counter in the update record equals 3
:to_state: STATE-ABANDONED
```

```{transition} battery < 20%
:id: TR-BATTERY-LOW
:kind: guard
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:condition: battery level falls below 20% at any point during download
:to_state: STATE-PAUSED
```

```{transition} next check: battery >= 20%
:id: TR-RESUME
:kind: guard
:source: brief §3
:part_of: LOOP-DOWNLOAD-RETRY
:condition: the next scheduled check runs and battery level is at least 20%; attempt counter is kept
:to_state: STATE-DOWNLOADING
```

## Requirements

```{requirement} never write to the active bank
:id: REQ-NO-ACTIVE-WRITE
:kind: safety
:source: brief §4
The updater SHALL never write to the active bank.
```

```{requirement} retry a failed download at most 3 times
:id: REQ-RETRY-LIMIT
:kind: functional
:source: brief §4
The updater SHALL retry a failed download at most 3 times per update.
```

```{requirement} roll back if health is not confirmed within 60 s
:id: REQ-AUTO-ROLLBACK
:kind: safety
:source: brief §4
The updater SHALL roll back automatically if health is not confirmed
within 60 s of reboot.
```

```{requirement} record every attempt, outcome and bank switch
:id: REQ-UPDATE-RECORD
:kind: functional
:source: brief §4
The updater SHALL record every attempt, outcome and bank switch in the
update record.
```

```{requirement} keep at least 20% battery
:id: REQ-BATTERY-RESERVE
:kind: operational
:source: brief §4
The device SHALL keep at least 20% battery for normal operation.
```

### Constraints

```{constraint} battery floor 20%
:id: CON-BATTERY-FLOOR
:kind: threshold
:source: brief §3
:limit: 20% battery
:derived_from: REQ-BATTERY-RESERVE
A download may not continue below 20% battery.
```

```{constraint} health confirmation window 60 s
:id: CON-HEALTH-TIMEOUT
:kind: threshold
:source: brief §2
:limit: 60 s after reboot
:derived_from: REQ-AUTO-ROLLBACK
The new firmware must report healthy within 60 s of reboot.
```

### Scenarios

```{scenario} verified image goes to the inactive bank only
:id: SC-WRITE-INACTIVE
:kind: nominal
:source: brief §4
:verifies: REQ-NO-ACTIVE-WRITE
WHEN an image has passed checksum and signature verification
THEN the updater writes it to the inactive bank and the active bank's
contents are unchanged.
```

```{scenario} second attempt after a first mismatch
:id: SC-RETRY-SECOND
:kind: nominal
:source: brief §4
:verifies: REQ-RETRY-LIMIT
WHEN the first download attempt fails verification and the attempt counter
is 1
THEN the updater starts a second download attempt and the counter becomes 2.
```

```{scenario} no fourth attempt
:id: SC-RETRY-EXHAUSTED
:kind: boundary
:source: brief §4
:verifies: REQ-RETRY-LIMIT
WHEN the third download attempt fails verification
THEN the updater abandons the update, records the outcome, and sleeps
until the next check without starting a fourth attempt.
```

```{scenario} rollback on missing health report
:id: SC-HEALTH-TIMEOUT
:kind: failure
:source: brief §4
:verifies: REQ-AUTO-ROLLBACK
WHEN 60 s have passed since reboot and no healthy report has arrived
THEN the device reboots into the previous bank and the update record marks
the update as failed.
```

```{scenario} healthy report in time
:id: SC-HEALTH-OK
:kind: nominal
:source: brief §4
:verifies: REQ-AUTO-ROLLBACK
WHEN a healthy report arrives within 60 s of reboot
THEN no rollback happens and the new bank is marked active.
```

```{scenario} attempt and outcome are recorded
:id: SC-RECORD-ATTEMPT
:kind: nominal
:source: brief §4
:verifies: REQ-UPDATE-RECORD
WHEN a download attempt ends, in success or failure
THEN the update record holds the attempt number and its outcome.
```

```{scenario} bank switch is recorded
:id: SC-RECORD-SWITCH
:kind: nominal
:source: brief §4
:verifies: REQ-UPDATE-RECORD
WHEN the new bank is marked active or the device rolls back
THEN the update record holds the bank switch and which bank is now active.
```

```{scenario} download pauses on low battery
:id: SC-BATTERY-PAUSE
:kind: boundary
:source: brief §4
:verifies: REQ-BATTERY-RESERVE
WHEN battery falls below 20% while chunks are being downloaded
THEN the download pauses, no further chunks are fetched, and the attempt
counter is unchanged.
```

```{scenario} download resumes at the next check
:id: SC-BATTERY-RESUME
:kind: nominal
:source: brief §4
:verifies: REQ-BATTERY-RESERVE
WHEN a paused download exists and the next check runs with battery at or
above 20%
THEN the download resumes from the verified chunks with the same attempt
counter.
```

## Views

Update sequence: actions and decisions with their pass, fail and re-entry
paths. The loop is included so that its `reenters` edge is drawn.

```{needflow} update sequence
:filter: type in ["action", "decision", "loop"] and docname == "example-ota"
:link_types: flows_to, fails_to, reenters
:config: lr
```

Download retry loop: its states and transitions.

```{needflow} download retry loop
:filter: type in ("state", "transition") and "LOOP-DOWNLOAD-RETRY" in part_of and docname == "example-ota"
:link_types: flows_to, to_state
:config: lr
```

Requirement coverage: scenarios and the requirements they verify.

```{needflow} requirement coverage
:filter: type in ["requirement", "scenario"] and docname == "example-ota"
:link_types: verifies
:config: lr
```

Loops.

```{needtable} loops
:filter: type == "loop" and docname == "example-ota"
:columns: id, title, limit, measure, reenters
```
