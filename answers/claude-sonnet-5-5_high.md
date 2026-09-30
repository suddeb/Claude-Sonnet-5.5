## The Risk

Salesforce enforces a limit of **100 synchronous SOQL queries per transaction** (200 async). A trigger fires once per batch of up to 200 records. If a SOQL query sits inside a `for` loop over `Trigger.new`, it executes once per record. A bulk insert, data load, or API call with more than 100 Cases throws `System.LimitException: Too many SOQL queries: 101`, and the entire transaction rolls back.

It also works fine in single-record UI testing, so the bug often only surfaces in production during bulk operations. Other automation in the same transaction (flows, other triggers) shares the same limit, making it worse.

## Anti-Pattern

```apex
trigger CaseTrigger on Case (before insert) {
    for (Case c : Trigger.new) {
        // SOQL in loop: 1 query per Case
        Account a = [SELECT Id, Name, Industry FROM Account WHERE Id = :c.AccountId];
        if (a.Industry == 'Healthcare') {
            c.Priority = 'High';
        }
    }
}
```

## Bulkified Rewrite

```apex
trigger CaseTrigger on Case (before insert) {
    // 1. Collect IDs
    Set<Id> accountIds = new Set<Id>();
    for (Case c : Trigger.new) {
        if (c.AccountId != null) {
            accountIds.add(c.AccountId);
        }
    }

    // 2. Single query, outside the loop
    Map<Id, Account> accountMap = new Map<Id, Account>(
        [SELECT Id, Name, Industry FROM Account WHERE Id IN :accountIds]
    );

    // 3. Loop and use the map
    for (Case c : Trigger.new) {
        Account a = accountMap.get(c.AccountId);
        if (a != null && a.Industry == 'Healthcare') {
            c.Priority = 'High';
        }
    }
}
```

**Result:** 1 query regardless of batch size. The same pattern applies to DML: collect records in a list and perform one `update` after the loop. As a best practice, move logic into a handler class and keep the trigger thin.