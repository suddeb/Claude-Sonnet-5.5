## The risk (≈110 words)

Salesforce allows **100 SOQL queries per synchronous transaction** (200 async). A trigger receives up to **200 records per batch**, so a query inside a `for` loop uses one query per Case. Testing one record in the UI works, but a data load, API call, or bulk update pushes the count past 100 and throws `System.LimitException: Too many SOQL queries: 101`. The whole transaction rolls back.

The limit is shared across every trigger, flow, and process in the transaction, so this trigger can also break unrelated automation. Queries in loops are also slow and burn CPU time.

## Anti-pattern (assumed example)

```apex
trigger CaseTrigger on Case (before insert) {
    for (Case c : Trigger.new) {
        // 1 query per Case
        Account a = [SELECT Id, SLA__c FROM Account WHERE Id = :c.AccountId];
        c.SLA_Tier__c = a.SLA__c;
    }
}
```

This also throws a `QueryException` when `AccountId` is null and no row is returned.

## Bulkified rewrite

```apex
trigger CaseTrigger on Case (before insert, before update) {
    CaseTriggerHandler.setSlaTier(Trigger.new);
}
```

```apex
public with sharing class CaseTriggerHandler {
    public static void setSlaTier(List<Case> cases) {
        // 1. Collect IDs
        Set<Id> accountIds = new Set<Id>();
        for (Case c : cases) {
            if (c.AccountId != null) {
                accountIds.add(c.AccountId);
            }
        }
        if (accountIds.isEmpty()) return;

        // 2. One query outside the loop
        Map<Id, Account> accountsById = new Map<Id, Account>(
            [SELECT Id, SLA__c FROM Account WHERE Id IN :accountIds]
        );

        // 3. Use the map in the loop
        for (Case c : cases) {
            Account a = accountsById.get(c.AccountId);
            if (a != null) {
                c.SLA_Tier__c = a.SLA__c;
            }
        }
        // Before trigger: no DML needed, the changes save automatically
    }
}
```

**Key points**
- Use **one query per object**, not per record: `Set` → `IN :set` → `Map`.
- In *after* triggers, add modified records to a list and run **one DML statement** outside the loop.
- Keep logic in a handler class so it's testable. Include a test that inserts 200+ Cases.