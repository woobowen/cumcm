# ARCH-W1-WORKFLOW-ONLY-GUARDS

W1 implements the four frozen specifications as a small set of stateless workflow
checklists.  It deliberately has no persistent evidence kernel or second state
controller: the adapter reads an immutable case, runs one bounded checklist, and
returns a reason-coded proposal.  `MAIN_AGENT_FORMAL_STATE_WRITER` remains the only
actor that may apply a formal transition.

Unknown or incomplete evidence fails closed.  Narrative overrides never bypass a
check.  The code neither imports nor calls the formal Skill, third-party content,
the network, or the sealed benchmark vault.
