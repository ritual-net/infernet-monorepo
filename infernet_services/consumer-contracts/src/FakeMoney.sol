// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {ERC20} from "solady/tokens/ERC20.sol";

contract FakeMoney is ERC20 {

    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }

    function name() public view override returns (string memory) {
        return "FakeMoney";
    }

    function symbol() public view override returns (string memory) {
        return "FM";
    }
}

contract AcceptedMoney is FakeMoney {}

contract RejectedMoney is FakeMoney {}
