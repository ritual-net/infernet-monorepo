// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {SubscriptionConsumer} from "infernet-sdk/consumer/Subscription.sol";
import {console2} from "forge-std/console2.sol";

contract GenericSubscriptionConsumer is SubscriptionConsumer  {
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
        string calldata containerId,
        uint48 maxGasPrice,
        uint32 maxGasLimit,
        uint32 frequency,
        uint32 period,
        uint16 redundancy
    ) public returns (uint256 subscriptionId){
        return _createComputeSubscription(containerId, maxGasPrice, maxGasLimit, frequency, period, redundancy);
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
        bytes calldata proof
    ) internal override {
        receivedOutputs.push(output);
    }
}
