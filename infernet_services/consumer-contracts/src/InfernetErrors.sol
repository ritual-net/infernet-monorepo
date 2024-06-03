// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.19;

import {console2} from "forge-std/console2.sol";
import {Registry} from "infernet-sdk/Registry.sol";
import {Wallet} from "infernet-sdk/payments/Wallet.sol";
import {Allowlist} from "infernet-sdk/pattern/Allowlist.sol";
import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {EIP712Coordinator} from "infernet-sdk/EIP712Coordinator.sol";

/// @title InfernetErrors
/// @notice Contract to test Infernet error handling.
/// @dev This contract raises the same errors in our Consumer, to test error
/// handling in infernet-node's logs.
contract InfernetErrors is CallbackConsumer, EIP712Coordinator, Allowlist {
    string private EXTREMELY_COOL_BANNER = "                 \n\n"
        " _____   _____ _______ _    _           _               \n"
        "|  __ \\|_   _|__   __| |  | |  /\\    | |             \n"
        "| |__) |  | |    | |  | |  | | /  \\   | |              \n"
        "|  _  /   | |    | |  | |  | |/ /\\\\  | |             \n"
        "| | \\ \\ _| |_  | |  | |__| / ____ \\ | |____        \n"
        "|_|  \\_\\_____| |_|  \\____/_/    \\_\\______|   \n\n";

    // Wallet's errors
    error TransferFailed();
    error InsufficientFunds();
    error InsufficientAllowance();

    constructor(Registry registry)
        CallbackConsumer(address(registry))
        EIP712Coordinator(registry)
        Allowlist(new address[](0))
    {}

    /// @notice Request a compute job to echo the errorId.
    /// @param errorId The errorId to echo.
    /// @dev Based on the returned errorId, the contract will revert with the corresponding error. This is then
    /// caught by our tests.
    function echoThis(string calldata errorId) public {
        _requestCompute(
            "echo",
            abi.encode(errorId, ""),
            1, // redundancy
            address(0), // paymentToken
            0, // paymentAmount
            address(0), // wallet
            address(0) // prover
        );
    }

    function strCmp(string memory a, string memory b) internal pure returns (bool) {
        return keccak256(abi.encodePacked(a)) == keccak256(abi.encodePacked(b));
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
        console2.log(EXTREMELY_COOL_BANNER);
        (bytes memory raw_input, bytes memory processed_input) = abi.decode(input, (bytes, bytes));
        (string memory errorIndex) = abi.decode(raw_input, (string));

        // Coordinator Errors
        if (strCmp(errorIndex, "1")) {
            // 0x23455ba1
            revert InvalidWallet();
        }

        if (strCmp(errorIndex, "2")) {
            // 0x4db310c3
            revert IntervalMismatch();
        }

        if (strCmp(errorIndex, "3")) {
            // 0x2f4ca85b
            revert IntervalCompleted();
        }

        if (strCmp(errorIndex, "4")) {
            // 0x8ebcfe1e
            revert UnauthorizedProver();
        }

        if (strCmp(errorIndex, "5")) {
            // 0x88a21e4f
            revert NodeRespondedAlready();
        }

        if (strCmp(errorIndex, "6")) {
            // 0x1a00354f
            revert SubscriptionNotFound();
        }

        if (strCmp(errorIndex, "7")) {
            // 0x1d68b37c
            revert ProofRequestNotFound();
        }

        if (strCmp(errorIndex, "8")) {
            // 0xa7fba711
            revert NotSubscriptionOwner();
        }

        if (strCmp(errorIndex, "9")) {
            // 0xae6704a7
            revert SubscriptionCompleted();
        }

        if (strCmp(errorIndex, "10")) {
            // 0xefb74efe
            revert SubscriptionNotActive();
        }

        if (strCmp(errorIndex, "11")) {
            // 0xa1e29b31
            revert UnsupportedProverToken();
        }

        // EIP712Coordinator errors
        if (strCmp(errorIndex, "12")) {
            // 0x10c74b03
            revert SignerMismatch();
        }

        if (strCmp(errorIndex, "13")) {
            // 0x0819bdcd
            revert SignatureExpired();
        }

        // Wallet errors
        if (strCmp(errorIndex, "14")) {
            // 0x90b8ec18
            revert TransferFailed();
        }

        if (strCmp(errorIndex, "15")) {
            // 0x356680b7
            revert InsufficientFunds();
        }

        if (strCmp(errorIndex, "16")) {
            // 0x13be252b
            revert InsufficientAllowance();
        }

        // Consumer Errors
        if (strCmp(errorIndex, "17")) {
            // 0x42764946
            revert NodeNotAllowed();
        }

        console2.log("input was", errorIndex);
    }
}
