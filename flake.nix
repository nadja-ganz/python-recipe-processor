{
  description = "Simple Python Hello World with Nix";

  outputs = { self, nixpkgs }: {
    devShell.x86_64-linux = nixpkgs.legacyPackages.x86_64-linux.mkShell {
      buildInputs = [
        nixpkgs.python3
        nixpkgs.git
      ];
    };
  };
}
