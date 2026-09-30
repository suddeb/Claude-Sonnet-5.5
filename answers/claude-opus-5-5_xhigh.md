## Governor-Limit Risk

Salesforce allows **100 SOQL queries per synchronous transaction** (200 asynchronous). Triggers process records in chunks of up to **200**, whether they come from Data Loader, API integrations, mass updates, or Flows. A query inside the loop runs once per Case, so a batch of 101+ Cases throws `System.LimitException: Too many SOQL queries: 101`, and the **entire transaction rolls back**.

The problem is often worse than that. The limit is shared across the whole transaction, so other triggers, flows, and managed packages draw from the same budget. Failures can occur with far fewer records.

The code usually passes single-record UI testing, then breaks in production during a data load.

**Fix:** Collect IDs into a `Set`, run one query outside the loop, store the results in a `Map`, then look records up in memory. The query count stays constant regardless of batch size.

---

## Before (Anti-Pattern)

```apex
trigger CaseTrigger on Case (before insert, before update) {
    for (Case c : Trigger.new) {
        if (c.AccountId != null) {
            // One query PER record: fails at 101 records
            Account a = [SELECT Rating FROM Account WHERE Id = :c.AccountId];
            if (a.Rating == 'Hot') {
                c.Priority = 'High';
            }
        }
    }
}
```

## After (Bulkified)

```apex
trigger CaseTrigger on Case (before insert, before update) {

    // 1. Collect parent IDs
    Set<Id> accountIds = new Set<Id>();
    for (Case c : Trigger.new) {
        if (c.AccountId != null) {
            accountIds.add(c.AccountId);
        }
    }
    if (accountIds.isEmpty()) {
        return;
    }

    // 2. ONE query for the entire batch
    Map<Id, Account> accountsById = new Map<Id, Account>(
        [SELECT Id, Rating FROM Account WHERE Id IN :accountIds]
    );

    // 3. In-memory lookup, no SOQL in the loop
    for (Case c : Trigger.new) {
        Account a = accountsById.get(c.AccountId);
        if (a != null && a.Rating == 'Hot') {
            c.Priority = 'High';
        }
    }
}
```

**Further improvements:**
- Move the logic into a handler class so there is one trigger per object.
- On update, process only Cases whose `AccountId` changed. Compare against `Trigger.oldMap`.
- Write a test that inserts 200+ Cases to prove the trigger is bulk-safe.