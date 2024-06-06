// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {SubscriptionConsumer} from "infernet-sdk/consumer/Subscription.sol";
import {console2} from "forge-std/console2.sol";
import {Delegator} from "infernet-sdk/pattern/Delegator.sol";

contract GenericCallbackConsumer is CallbackConsumer, Delegator {
    mapping(uint32 => bytes) public receivedInput;
    mapping(uint32 => bytes) public receivedOutput;
    mapping(uint32 => bytes) public receivedProof;

    // Flag to check if the compute was received since the last request
    bool public receivedToggle;
    bytes public lastOutput;

    constructor(address registry, address signer) CallbackConsumer(registry) Delegator(signer) {
        console2.log("registry address", address(registry));
        console2.log("signer address", address(signer));
        console2.log("coordinators address", address(COORDINATOR));
    }

    function requestCompute(
        string memory containerId,
        bytes memory inputs,
        uint16 redundancy,
        address paymentToken,
        uint256 paymentAmount,
        address wallet,
        address verifier
    ) public returns (uint32) {
        uint32 id = _requestCompute(containerId, inputs, redundancy, paymentToken, paymentAmount, wallet, verifier);
        console2.log("Made subscription request", id);
        return id;
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
        console2.log("GenericCallbackConsumer: Received compute for subscription", subscriptionId);
        receivedToggle = !receivedToggle;
        lastOutput = output;

        receivedInput[subscriptionId] = input;
        receivedOutput[subscriptionId] = output;
        receivedProof[subscriptionId] = proof;
    }
}
