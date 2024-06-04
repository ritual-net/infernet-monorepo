// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {SubscriptionConsumer} from "infernet-sdk/consumer/Subscription.sol";
import {console2} from "forge-std/console2.sol";

contract GenericSubscriptionConsumer is SubscriptionConsumer {
    mapping(uint32 => bytes) public receivedInput;
    mapping(uint32 => bytes) public receivedOutput;
    mapping(uint32 => bytes) public receivedProof;
    mapping(uint32 => bytes) public containerInput;

    constructor(address registry) SubscriptionConsumer(registry) {}

    function getContainerInputs(uint32 subscriptionId, uint32 interval, uint32 timestamp, address caller)
        external
        view
        override
        returns (bytes memory)
    {
        return containerInput[subscriptionId];
    }

    function setSubscriptionInput(uint32 subscriptionId, bytes calldata input) external {
        containerInput[subscriptionId] = input;
    }

    function createSubscription(
        bytes memory input,
        string memory containerId,
        uint32 frequency,
        uint32 period,
        uint16 redundancy,
        bool lazy,
        address paymentToken,
        uint256 paymentAmount,
        address wallet,
        address prover
    ) public virtual returns (uint32) {
        uint32 subId = _createComputeSubscription(
            containerId, frequency, period, redundancy, lazy, paymentToken, paymentAmount, wallet, prover
        );
        containerInput[subId] = input;
        return subId;
    }

    function cancelSubscription(uint32 subscriptionId) public {
        COORDINATOR.cancelSubscription(subscriptionId);
    }

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
    ) internal virtual override {
        console2.log("GenericSubscriptionConsumer: Received compute for subscription", subscriptionId);
        receivedInput[subscriptionId] = input;
        receivedOutput[subscriptionId] = output;
        receivedProof[subscriptionId] = proof;
    }
}
