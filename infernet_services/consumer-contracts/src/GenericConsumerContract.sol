// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";

contract GenericConsumerContract is CallbackConsumer {
    bytes public receivedInput;
    bytes public receivedOutput;
    bytes public receivedProof;

    constructor(address coordinator) CallbackConsumer(coordinator) {}

    function requestCompute(string calldata containerId, bytes calldata inputs) public {
        _requestCompute(containerId, inputs, 20 gwei, 1_000_000, 1);
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
        receivedInput = input;
        receivedOutput = output;
        receivedProof = proof;
    }
}
