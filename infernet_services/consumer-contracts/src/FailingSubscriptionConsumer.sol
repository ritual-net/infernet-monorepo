// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {console2} from "forge-std/console2.sol";
import {DelegateSubscriptionConsumer} from "./DelegateSubscriptionConsumer.sol";

contract FailingSubscriptionConsumer is DelegateSubscriptionConsumer {
    constructor(address _coordinator, address _signer) DelegateSubscriptionConsumer(_coordinator, _signer) {}

    function _receiveCompute(
        uint32 subscriptionId,
        uint32 interval,
        uint16 redundancy,
        address node,
        bytes calldata input,
        bytes calldata output,
        bytes calldata proof,
        bytes32 containerId,
        uint256 index
    ) internal override {
        receivedOutputs.push(output);
        console2.log("received output");
        console2.logBytes(output);
        revert("reverting");
    }
}
