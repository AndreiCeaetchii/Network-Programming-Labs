/**
 * Deferred represents a Promise that can be resolved or rejected externally.
 * This is useful for implementing waiting/notification patterns.
 *
 * Example usage:
 *   const deferred = new Deferred<number>();
 *   setTimeout(() => deferred.resolve(42), 1000);
 *   const result = await deferred.promise; // waits for 1 second, then result = 42
 */
export class Deferred {
    promise;
    resolveFn;
    rejectFn;
    constructor() {
        this.promise = new Promise((resolve, reject) => {
            this.resolveFn = resolve;
            this.rejectFn = reject;
        });
    }
    /**
     * Resolve this deferred promise with a value
     */
    resolve(value) {
        this.resolveFn(value);
    }
    /**
     * Reject this deferred promise with an error
     */
    reject(reason) {
        this.rejectFn(reason);
    }
}
//# sourceMappingURL=Deferred.js.map