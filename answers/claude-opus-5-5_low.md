## The Governor-Limit Risk

Salesforce limits synchronous Apex to **100 SOQL queries per transaction**. Triggers receive records in batches of up to 200, and Data Loader, integrations, or bulk API jobs routinely send full batches. A query inside a `for` loop runs once per record, so 200 Cases means 200 queries. The transaction then fails with `System.LimitException: Too many SOQL queries: 101`, and the entire DML operation rolls back.

The problem compounds. Other triggers, flows, and process automation in the same transaction share the same 100-query budget, so the failure can surface far from the offending code, even with batches under 100. Row limits (50,000) and CPU time (10s) also suffer from repeated round-trips.

The fix is **bulkification**: collect IDs first, query once with `IN`, store results in a `Map`, then loop and look up values in memory.

---

## Anti-Pattern (Before)

```apex
trigger CaseTrigger on Case (before insert, before update) {
    for (Case c : Trigger.new) {
        // One query PER record: fails at 101 records
        Account acc = [SELECT Id, Support_Tier__c
                       FROM Account
                       WHERE Id = :c.AccountId];
        if (acc.Support_Tier__c == 'Premium') {
            c.Priority = 'High';
        }
    }
}
```

## Bulkified Rewrite (After)

```apex
trigger CaseTrigger on Case (before insert, before update) {

    // 1. Collect all related Account IDs (Set removes duplicates)
    Set<Id> accountIds = new Set<Id>();
    for (Case c : Trigger.new) {
        if (c.AccountId != null) {
            accountIds.add(c.AccountId);
        }
    }

    if (accountIds.isEmpty()) {
        return;
    }

    // 2. ONE query for the whole batch, loaded into a Map for O(1) lookup
    Map<Id, Account> accountMap = new Map<Id, Account>(
        [SELECT Id, Support_Tier__c
         FROM Account
         WHERE Id IN :accountIds]
    );

    // 3. Loop again, using in-memory lookups only (no SOQL)
    for (Case c : Trigger.new) {
        Account acc = accountMap.get(c.AccountId);
        if (acc != null && acc.Support_Tier__c == 'Premium') {
            c.Priority = 'High';
        }
    }
}
```

### Key Improvements
| Aspect | Before | After |
|---|---|---|
| SOQL queries (200 Cases) | 200 (fails) | **1** |
| Null `AccountId` handling | Throws `QueryException` | Safely skipped |
| Duplicate Accounts | Queried repeatedly | Deduplicated via `Set` |

**Best practice:** Move this logic into a handler class (e.g., `CaseTriggerHandler`) to keep one trigger per object and make unit testing easier. Test with **200+ records** to prove the code is bulk-safe.