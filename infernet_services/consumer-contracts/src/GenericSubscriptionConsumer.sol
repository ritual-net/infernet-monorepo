// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {SubscriptionConsumer} from "infernet-sdk/consumer/Subscription.sol";
import {console2} from "forge-std/console2.sol";

contract GenericSubscriptionConsumer is SubscriptionConsumer {
    bytes[] public receivedOutputs;

    constructor(address coordinator) SubscriptionConsumer(coordinator) {}

    bytes public input;

    function setInput(bytes calldata _input) public {
        input = _input;
    }

    function getReceivedOutputs() public view returns (bytes[] memory) {
        return receivedOutputs;
    }

    function getContainerInputs(uint32 subscriptionId, uint32 interval, uint32 timestamp, address caller)
        external
        view
        override
        returns (bytes memory)
    {
        return input;
    }

    function createSubscription(
        string memory containerId,
        uint32 frequency,
        uint32 period,
        uint16 redundancy,
        bool lazy,
        address paymentToken,
        uint256 paymentAmount,
        address wallet,
        address prover
    ) public returns (uint256 subscriptionId) {
        return _createComputeSubscription(
            containerId, frequency, period, redundancy, lazy, paymentToken, paymentAmount, wallet, prover
        );
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
        receivedOutputs.push(output);
        console2.log("received output!");
        console2.logBytes(output);
    }
}
