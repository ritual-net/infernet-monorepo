// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {SubscriptionConsumer} from "infernet-sdk/consumer/Subscription.sol";
import {console2} from "forge-std/console2.sol";
import {Delegator} from "infernet-sdk/pattern/Delegator.sol";

contract GenericCallbackConsumer is CallbackConsumer, Delegator {
    mapping(bytes32 => bytes) public receivedInput;
    mapping(bytes32 => bytes) public receivedOutput;
    mapping(bytes32 => bytes) public receivedProof;

    // Flag to check if the compute was received since the last request
    bool public receivedToggle;
    bytes public lastOutput;

    constructor(address registry, address signer) CallbackConsumer(registry) Delegator(signer) {
        console2.log("registry address", address(registry));
        console2.log("signer address", address(signer));
        console2.log("coordinators address", address(COORDINATOR));
    }

    function requestCompute(
        string memory randomness,
        string memory containerId,
        bytes memory inputs,
        uint16 redundancy,
        address paymentToken,
        uint256 paymentAmount,
        address wallet,
        address prover
    )
        public
        returns (bytes32)
    {
        bytes32 generatedTaskId = keccak256(abi.encodePacked(inputs, randomness));
        console2.log("generated task id, now requesting compute");
        console2.logBytes32(generatedTaskId);
        _requestCompute(
            containerId,
            abi.encodePacked(inputs, randomness),
            redundancy,
            paymentToken,
            paymentAmount,
            wallet,
            prover
        );
        console2.log("requested compute");
        return generatedTaskId;
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
    ) internal override {
        (bytes memory raw, bytes memory processed) = abi.decode(input, (bytes, bytes));
        bytes32 taskId = keccak256(raw);
        console2.log("Received compute");
        console2.logBytes32(taskId);
        receivedToggle = !receivedToggle;
        lastOutput = output;
        receivedInput[taskId] = input;
        receivedOutput[taskId] = output;
        receivedProof[taskId] = proof;
    }
}
