// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {SubscriptionConsumer} from "infernet-sdk/consumer/Subscription.sol";

contract GenericCallbackConsumer is CallbackConsumer {
    mapping(bytes32 => bytes) public receivedInput;
    mapping(bytes32 => bytes) public receivedOutput;
    mapping(bytes32 => bytes) public receivedProof;

    constructor(address coordinator) CallbackConsumer(coordinator) {}

    function requestCompute(string calldata containerId, string memory randomness, bytes calldata inputs)
        public
        returns (bytes32)
    {
        bytes32 generatedTaskId = keccak256(abi.encodePacked(inputs, randomness));
        _requestCompute(containerId, abi.encodePacked(inputs, randomness), 20 gwei, 1_000_000, 1);
        return generatedTaskId;
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
        (bytes memory raw, bytes memory processed) = abi.decode(input, (bytes, bytes));
        bytes32 taskId = keccak256(raw);
        receivedInput[taskId] = input;
        receivedOutput[taskId] = output;
        receivedProof[taskId] = proof;
    }
}
