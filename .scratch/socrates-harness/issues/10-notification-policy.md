# 10 — Notification policy: quiet by default

**What to build:** The harness is quiet by default — routine Probes and Interviews are not Notifications. It interrupts the user only for unavoidable conflicts (cannot be deferred, block progress) and Supersede cascades removing interdependent Propositions. Delivery channels (push, email, in-app) are an implementation detail, stubbed behind the Notification boundary.

**Blocked by:** 06 — Supersede cascade (for cascade notifications); 08 — Deferral (defines "unavoidable" as non-deferrable).

**Status:** ready-for-agent

- [ ] Routine Probes and Interviews produce no Notification.
- [ ] An unavoidable conflict (non-deferrable, blocks progress) triggers a Notification.
- [ ] A Supersede cascade removing interdependent Propositions triggers a Notification.
- [ ] Delivery channels are stubbed behind the Notification boundary.
