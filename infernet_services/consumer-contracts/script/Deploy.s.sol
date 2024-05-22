// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {Script, console2} from "forge-std/Script.sol";
import {BetterDeployer} from "better-deployer/BetterDeployer.sol";

contract Deploy is BetterDeployer {
    function strCmp(string memory a, string memory b) private returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function run() public {
        // Setup wallet
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        string memory filename = vm.envString("filename");
        string memory contractName = vm.envString("contract");
        address coordinator = vm.envAddress("coordinator");
        address signer = vm.envAddress("signer");
        vm.startBroadcast(deployerPrivateKey);

        // set filename
        setPathAndFile("deployments", "deployments.json");

        // Log address
        address deployerAddress = vm.addr(deployerPrivateKey);
        console2.log("Loaded deployer: ", deployerAddress);
        console2.log("Coordinator: ", coordinator);

        string memory artifact = string.concat("./out/", filename, "/", contractName, ".json");
        address consumer;
        if (signer != address(0)) {
            console2.log("Signer: ", signer);
            consumer = deploy(contractName, artifact, abi.encode(coordinator, signer));
        } else {
            consumer = deploy(contractName, artifact, abi.encode(coordinator));
        }

        console2.log("Deployed Contract: ", address(consumer));

        // dump deployed contract addresses to file
        dump();

        // Broadcast
        vm.stopBroadcast();
        vm.broadcast();
    }
}
