import os
import toolutils

from oli.Gallery import GalleryModel


class DefaultBackend(object):
    """
    The Default Backend Strategy.
    Responsibility: File System Scanning & Houdini Node Creation.
    """

    def __init__(self, model: GalleryModel):
        self.model = model

    # ----------------------------------------------------------------------
    # Data Fetching (Implicit Interface)
    # ----------------------------------------------------------------------

    def collectionsList(self):
        """
        Returns a list of collection names (folders) in the current root.
        """
        root = self.model.currentRoot
        if os.path.exists(root):
            try:
                # List directories only
                return sorted(
                    [
                        d
                        for d in os.listdir(root)
                        if os.path.isdir(os.path.join(root, d))
                    ]
                )
            except Exception as e:
                print(f"Error listing collections: {e}")
                return []
        return []

    def collectionChanged(self):
        """Optional hook if you need to reset internal caches."""
        pass

    def getAssetsData(self):
        """
        Scans the current path and returns a list of dictionaries.
        This replaces 'createItems' and 'ItemCreator'.
        """
        root = self.model.currentRoot
        collection = self.model.currentCollection
        path = os.path.join(root, collection)

        if not os.path.exists(path):
            return []

        assetsDataList = []

        # Scan immediate subdirectories as assets
        try:
            assetFolders = sorted(next(os.walk(path))[1])
        except StopIteration:
            return []

        for assetName in assetFolders:
            assetPath = os.path.join(path, assetName).replace("\\", "/")

            # Construct the Data Object
            # This dict contains EVERYTHING the View needs to draw the item
            data = {
                "id": f"{collection}/{assetName}",
                "asset_name": assetName,
                "asset_display_name": assetName.replace("_", " "),
                "full_path": assetPath,
                "thumbnail_path": self._find_thumbnail(assetPath),
                "category": self._detect_category(assetPath),  # Helper logic
                # Add any other metadata parsing here (e.g. read a json file inside the folder)
                "geometry_path": self._find_geometry(assetPath),
                "tags": self.model.preferences.get("tags", {}).get(
                    f"{collection}/{assetName}", []
                ),
            }
            assetsDataList.append(data)

        return assetsDataList

    # ----------------------------------------------------------------------
    # Actions / Import Logic
    # ----------------------------------------------------------------------

    def importAssetData(self, asset_data):
        """
        The main import logic.
        Detects the context (Network Editor vs Scene Viewer) and acts accordingly.
        """
        asset_name = asset_data["asset_name"]
        collection = self.model.currentCollection

        # Check active pane to decide how to import
        pane = toolutils.activePane([])

        # 1. LOPs / Solaris Context (Scene Graph)
        if isinstance(pane, hou.SceneViewer) and pane.isViewingSceneGraph():
            return self._import_usd_sublayer(asset_data, pane)

        # 2. Standard Network Editor Import
        # Fallback to standard object creation or specific logic
        utils.flashMessage(f"Importing {asset_name}...", 2)
        return None  # Return the node created if applicable

    def _import_usd_sublayer(self, asset_data, pane):
        """Helper for USD imports."""
        if not asset_data.get("geometry_path"):
            print("No geometry path found for asset.")
            return None

        node = pane.pwd()
        # Create unique name
        node_name = utils.makeSafe(f"{asset_data['asset_name']}")

        n_sublayer = node.createNode("sublayer", node_name)
        n_sublayer.parm("filepath1").set(asset_data["geometry_path"])
        n_sublayer.setSelected(True, True)
        n_sublayer.setGenericFlag(hou.nodeFlag.Display, True)

        # Connect to selected node if exists
        selection = hou.selectedNodes()
        if selection:
            n_sublayer.setInput(0, selection[-1])

        return n_sublayer

    # ----------------------------------------------------------------------
    # Helper / Utility Methods
    # ----------------------------------------------------------------------

    def _find_thumbnail(self, asset_path):
        """Simple heuristic to find a thumbnail."""
        # You can expand this list or make it a preference
        valid_exts = [".jpg", ".png", ".exr"]

        # 1. Check for 'thumbnail.jpg' inside
        for ext in valid_exts:
            thumb = os.path.join(asset_path, "thumbnail" + ext)
            if os.path.exists(thumb):
                return thumb.replace("\\", "/")

        return None

    def _find_geometry(self, asset_path):
        """Simple heuristic to find the main usd/geo file."""
        for f in os.listdir(asset_path):
            if f.endswith(".usd") or f.endswith(".usdc"):
                return os.path.join(asset_path, f).replace("\\", "/")
        return None

    def _detect_category(self, asset_path):
        """
        Legacy logic support:
        If you have a sidecar file or directory structure defining categories, read it here.
        """
        return ""

    # ----------------------------------------------------------------------
    # Context Menu / Drag & Drop Actions
    # ----------------------------------------------------------------------

    def openInExplorer(self, asset_data):
        """Action triggerable by the ViewModel."""
        if asset_data and "full_path" in asset_data:
            path = asset_data["full_path"]
            if os.path.exists(path):
                os.startfile(path)

    def createCollection(self, name):
        """Action triggerable by the ViewModel."""
        root = hou.text.expandString(self.parent_model.currentRoot)
        path = os.path.join(root, name)
        if not os.path.exists(path):
            os.makedirs(path)
            return True
        return False

    def handleDropEvent(self, mime_data, selected_assets_data):
        """
        Handles the logic when assets are dropped onto a Houdini pane.

        :param selected_assets_data: List of dicts (the assets currently selected in UI)
        """
        pane = hou.ui.curDesktop().paneTabUnderCursor()
        if not pane:
            return

        paneType = pane.type()

        # --- Network Editor Logic ---
        if paneType == hou.paneTabType.NetworkEditor:
            pos = pane.cursorPosition()

            for idx, asset in enumerate(selected_assets_data):
                node = self.importAssetData(asset)  # Reuse standard import logic
                if node:
                    node.setPosition(pos)
                    node.move((0, idx * -1.0))  # Stack vertically

        # --- Scene Viewer Logic ---
        elif paneType == hou.paneTabType.SceneViewer:
            # Check for layout state
            if pane.currentState() == "sidefx_lop_layout":
                # This would need a helper function to replicate your old `import_selected_assets_to_lop_layout`
                # accessing the `lookdev` module you had imported in the original file.
                pass
            else:
                for asset in selected_assets_data:
                    node = self.importAssetData(asset)
                    if node and hasattr(node, "moveToGoodPosition"):
                        node.moveToGoodPosition()
