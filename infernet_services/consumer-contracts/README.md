# Consumer Contracts

This directory contains a collection of consumer contracts used to test the Infernet
services, as well as the Infernet node itself.

## Contracts

* [GenericSubscriptionConsumer](./src/GenericSubscriptionConsumer.sol): A generic
  contract that can be used to make generalized subscriptions requests.
* [GenericCallbackConsumer](./src/GenericCallbackConsumer.sol): A generic contract
  that can be used to make generalized callback subscription requests.
* [DelegateSubscriptionConsumer](./src/DelegateSubscriptionConsumer.sol): A contract
  used to test the delegate subscription functionality.
* [FakeMoney.sol](./src/FakeMoney.sol): ERC20 token used for testing the payment
  functionality.
* [GenericVerifier.sol](./src/GenericVerifier.sol): Examples of an Eager & Lazy
  verifier contracts, used to test the verification functionality.
* [InfernetErrors](./src/InfernetErrors.sol): A contract used to generate errors
  for testing purposes.
* [FailingSubscriptionConsumer](./src/FailingSubscriptionConsumer.sol): A contract
  used to test the error handling functionality.
