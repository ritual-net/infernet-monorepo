// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {IVerifier} from "infernet-sdk/payments/IVerifier.sol";
import {Registry} from "infernet-sdk/Registry.sol";
import {EIP712Coordinator} from "infernet-sdk/EIP712Coordinator.sol";
import {WalletFactory} from "infernet-sdk/payments/WalletFactory.sol";

contract GenericAtomicVerifier is IVerifier {
    string private ACCEPTED_PROOF = "just trust me bro";
    address private wallet;
    mapping(address => bool) public acceptedPayments;
    mapping(address => uint256) public prices;
    Registry private registry;

    constructor(Registry _registry) {
        wallet = WalletFactory(_registry.WALLET_FACTORY()).createWallet(msg.sender);
        registry = _registry;
    }

    function disallowToken(address token) external {
        acceptedPayments[token] = false;
    }

    function setPrice(address token, uint256 price) external {
        acceptedPayments[token] = true;
        prices[token] = price;
    }

    function getWallet() external view override returns (address) {
        return wallet;
    }

    function isSupportedToken(address token) external view override returns (bool) {
        return acceptedPayments[token];
    }

    function fee(address token) external view override returns (uint256) {
        return prices[token];
    }

    function _finalizeProof(uint32 subscriptionId, uint32 interval, address node, bytes memory proof) internal {
        string memory content = abi.decode(proof, (string));
        EIP712Coordinator coordinator = EIP712Coordinator(registry.COORDINATOR());
        if (keccak256(abi.encodePacked(content)) == keccak256(abi.encodePacked(ACCEPTED_PROOF))) {
            coordinator.finalizeProofVerification(subscriptionId, interval, node, true);
        } else {
            coordinator.finalizeProofVerification(subscriptionId, interval, node, false);
        }
    }

    function requestProofVerification(uint32 subscriptionId, uint32 interval, address node, bytes calldata proof)
        external
        virtual
        override
    {
        _finalizeProof(subscriptionId, interval, node, proof);
    }

    receive() external payable {}
}

contract GenericLazyVerifier is GenericAtomicVerifier {
    constructor(Registry _registry) GenericAtomicVerifier(_registry) {}

    mapping(uint32 => mapping(uint32 => mapping(address => bytes))) public storedProofs;

    function requestProofVerification(uint32 subscriptionId, uint32 interval, address node, bytes calldata proof)
        external
        override
    {
        storedProofs[subscriptionId][interval][node] = proof;
    }

    function finalize(uint32 subscriptionId, uint32 interval, address node) external {
        bytes memory proof = storedProofs[subscriptionId][interval][node];
        _finalizeProof(subscriptionId, interval, node, proof);
    }
}
