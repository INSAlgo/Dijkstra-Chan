{
  description = "INSAlgo's discord beloved bot.";

  inputs = {
    nixpkgs.url = github:NixOS/nixpkgs/nixos-unstable;
    flake-utils.url = github:numtide/flake-utils;
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python311Packages;

        impurePythonEnv = pkgs.mkShell rec {
          name = "impurePythonEnv";
          venvDir = "./.venv";
          buildInputs = [
            pythonPackages.python
            pythonPackages.venvShellHook
            pkgs.autoPatchelfHook

            # broken imports from pip
            pythonPackages.matplotlib

            # necessary for some C++ related dependencies
            pkgs.gcc
            pkgs.autoPatchelfHook
          ];

          postVenvCreation = ''
            unset SOURCE_DATE_EPOCH
            pip install -r requirements.txt
            autoPatchelf ./venv
          '';

          postShellHook = ''
            unset SOURCE_DATE_EPOCH
          '';
        };
      in
      {
        devShells.default = impurePythonEnv;
      }
    );
  
}
