{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    futils.url = "github:numtide/flake-utils";
    poetry2nix.url = "github:nix-community/poetry2nix";
  };

  outputs = { self, nixpkgs, futils, poetry2nix } @ inputs:
    let
      inherit (nixpkgs) lib;
      inherit (lib) recursiveUpdate;
      inherit (futils.lib) eachDefaultSystem defaultSystems;

      nixpkgsFor = lib.genAttrs defaultSystems (system: import nixpkgs {
        inherit system;
        overlays = [
          poetry2nix.overlay
          self.overlay
        ];
      });

      poetryArgs = { pkgs, groups ? [ ] }: {
        projectDir = self;
        src = self;
        inherit groups;

        overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
          dataconf = super.dataconf.overridePythonAttrs (old: {
            buildInputs = old.buildInputs ++ [ self.poetry ];
          });
          pathspec = super.pathspec.overridePythonAttrs (old: {
            propagatedBuildInputs = old.propagatedBuildInputs ++ [ self.flit-core ];
          });
          pies = super.pies.overridePythonAttrs (old: {
            propagatedBuildInputs = old.propagatedBuildInputs ++ [ self.setuptools ];
          });
          pydocstyle = super.pydocstyle.overridePythonAttrs (old: {
            propagatedBuildInputs = old.propagatedBuildInputs ++ [ self.poetry ];
          });
          pyproject-hooks = super.pyproject-hooks.overridePythonAttrs (old: {
            propagatedBuildInputs = old.propagatedBuildInputs ++ [ self.flit-core ];
          });
          setoptconf-tmp = super.setoptconf-tmp.overridePythonAttrs (old: {
            buildInputs = old.buildInputs ++ [ self.setuptools ];
          });
        });

        meta = with lib; {
          inherit (self) description;
          maintainers = with maintainers; [ risson ];
        };
      };

      anySystemOutputs = {
        overlay = final: prev: {
          afs-tools = final.poetry2nix.mkPoetryApplication (poetryArgs { pkgs = final; });
        };
      };

      multipleSystemsOutputs = eachDefaultSystem (system:
        let
          pkgs = nixpkgsFor.${system};
        in
        {
          devShell = pkgs.mkShell {
            buildInputs = with pkgs; [
              git
              poetry
              ((pkgs.poetry2nix.mkPoetryEnv (removeAttrs (poetryArgs { inherit pkgs; groups = [ "dev" ]; }) [ "meta" "src" "propagatedBuildInputs" ])).override { ignoreCollisions = true; })
            ];

            PYTHONPATH = ".";
          };

          packages = {
            inherit (pkgs) afs-tools;
            default = pkgs.afs-tools;
          };

          apps = {
            afs-tools = {
              type = "app";
              program = "${self.packages.${system}.afs-tools}/bin/afs-tools";
            };
            default = {
              type = "app";
              program = "${self.packages.${system}.default}/bin/afs-tools";
            };
          };
        });
    in
    recursiveUpdate multipleSystemsOutputs anySystemOutputs;
}
