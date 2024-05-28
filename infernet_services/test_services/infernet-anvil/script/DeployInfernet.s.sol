// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "forge-std/Script.sol";
import {Registry} from "infernet-sdk/src/Registry.sol";
import {EIP712Coordinator} from "infernet-sdk/src/EIP712Coordinator.sol";
import {Inbox} from "infernet-sdk/src/Inbox.sol";
import {Reader} from "infernet-sdk/src/utility/Reader.sol";
import {Fee} from "infernet-sdk/src/payments/Fee.sol";
import {LibDeploy} from "infernet-sdk/test/lib/LibDeploy.sol";
import {WalletFactory} from "infernet-sdk/src/payments/WalletFactory.sol";

contract DeployInfernet is Script {
    function setUp() public {}

    function run() public {
        // Setup wallet
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        // Log address
        address deployerAddress = vm.addr(deployerPrivateKey);
        console.log("Loaded deployer: ", deployerAddress);

        // Get deployer address nonce
        uint256 initialNonce = vm.getNonce(deployerAddress);

        // Deploy contracts via LibDeploy
        (
            Registry registry,
            EIP712Coordinator coordinator,
            Inbox inbox,
            Reader reader,
            Fee fee,
            WalletFactory walletFactory
        ) = LibDeploy.deployContracts(initialNonce, deployerAddress, 500);

        // Log deployed contracts
        console.log("Using protocol fee: 5%");
        console.log("Deployed Registry: ", address(registry));
        console.log("Deployed EIP712Coordinator: ", address(coordinator));
        console.log("Deployed Inbox: ", address(inbox));
        console.log("Deployed Reader: ", address(reader));
        console.log("Deployed Fee: ", address(fee));
        console.log("Deployed WalletFactory: ", address(walletFactory));

        address initialOwner = vm.envAddress("payment_wallet_owner");

        address wallet = walletFactory.createWallet(initialOwner);
        console.log("Deployed Wallet: ", wallet);

        // Execute
        vm.stopBroadcast();
    }
}
