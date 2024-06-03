// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {Delegator} from "infernet-sdk/pattern/Delegator.sol";
import {GenericSubscriptionConsumer} from "./GenericSubscriptionConsumer.sol";

contract DelegateSubscriptionConsumer is GenericSubscriptionConsumer, Delegator {
    mapping(bytes32 => uint32) public subIdByInput;

    constructor(address _registry, address _signer) GenericSubscriptionConsumer(_registry) Delegator(_signer) {}

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
        super._receiveCompute(subscriptionId, interval, redundancy, node, input, output, proof, containerId, index);
        (bytes memory raw,) = abi.decode(input, (bytes, bytes));
        bytes32 inputHash = keccak256(raw);
        subIdByInput[inputHash] = subscriptionId;
    }
}
