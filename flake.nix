{
  description = "Python Recipe Processor";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonPackages = python.pkgs;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            pythonPackages.pdfplumber
            pythonPackages.pillow
            pythonPackages.pip
            pythonPackages.python-dotenv
            pythonPackages.openai
            # pythonPackages.anthropic  # Add if using Claude
          ];

          shellHook = ''
            echo "Python Recipe Processor environment loaded"
            echo "Python version: $(python --version)"
          '';
        };
      }
    );
}