// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.19;

import {console2} from "forge-std/console2.sol";
import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";
import {EIP712Coordinator} from "infernet-sdk/EIP712Coordinator.sol";

/// @title InfernetErrors
/// @notice Contract to test Infernet error handling.
/// @dev This contract raises the same errors in our Manager & Consumer, to test error
/// handling.
contract InfernetErrors is CallbackConsumer, EIP712Coordinator {
    string private EXTREMELY_COOL_BANNER = "\n\n" "_____  _____ _______ _    _         _                 \n"
        "|  __ \\|_   _|__   __| |  | |  /\\   | |             \n"
        "| |__) | | |    | |  | |  | | /  \\  | |              \n"
        "|  _  /  | |    | |  | |  | |/ /\\ \\ | |             \n"
        "| | \\ \\ _| |_   | |  | |__| / ____ \\| |____        \n"
        "|_|  \\_\\_____|  |_|   \\____/_/    \\_\\______|   \n\n";

    constructor(address coordinator) CallbackConsumer(coordinator) {}

    /// @notice Request a compute job to echo the errorId.
    /// @param errorId The errorId to echo.
    /// @dev Based on the returned errorId, the contract will revert with the corresponding error. This is then
    /// caught by our tests.
    function echoThis(uint8 errorId) public {
        _requestCompute("echo", abi.encode(errorId), 20 gwei, 1_000_000, 1);
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
        console2.log(EXTREMELY_COOL_BANNER);
        (bytes memory raw_input, bytes memory processed_input) = abi.decode(input, (bytes, bytes));
        (uint8 errorIndex) = abi.decode(raw_input, (uint8));

        // Handle error
        if (errorIndex == 1) {
            revert NodeNotActive();
        }

        if (errorIndex == 2) {
            revert NodeNotRegisterable(address(this), NodeStatus.Active);
        }

        if (errorIndex == 3) {
            revert CooldownActive(uint32(0));
        }

        if (errorIndex == 4) {
            revert NodeNotActivateable(NodeStatus.Active);
        }

        if (errorIndex == 5) {
            revert GasPriceExceeded();
        }

        if (errorIndex == 6) {
            revert GasLimitExceeded();
        }

        if (errorIndex == 7) {
            revert IntervalMismatch();
        }

        if (errorIndex == 8) {
            revert IntervalCompleted();
        }

        if (errorIndex == 9) {
            revert NodeRespondedAlready();
        }

        if (errorIndex == 10) {
            revert SubscriptionNotFound();
        }

        if (errorIndex == 11) {
            revert NotSubscriptionOwner();
        }

        if (errorIndex == 12) {
            revert SubscriptionCompleted();
        }

        if (errorIndex == 13) {
            revert SubscriptionNotActive();
        }

        console2.log("input was", errorIndex);
    }
}
