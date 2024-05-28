// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {console2} from "forge-std/console2.sol";
import {Delegator} from "infernet-sdk/pattern/Delegator.sol";
import {GenericSubscriptionConsumer} from "./GenericSubscriptionConsumer.sol";

contract DelegateSubscriptionConsumer is GenericSubscriptionConsumer, Delegator {
    constructor(address _coordinator, address _signer) GenericSubscriptionConsumer(_coordinator) Delegator(_signer) {}
}
