# ADR-0015: Non-self-referential verification state

Status: Accepted. `content_verified_commit` identifies an existing content commit and its manifest.
`delivery_receipt_for_commit` records remote verification for that same prior commit. The commit
containing these fields does not claim to verify or deliver itself.
