import os
import bpy
from .functions.global_settings import ProjectSettings, Extensions
from .functions.file_management import *
from .functions.animation import add_transform_effect
from .functions.sequences import find_empty_channel


# TODO: Refactor, walk directories and collect filepaths, then send to function
#       to create strips
# TODO: By default, do not reimport existing strips, import only the new ones
# TODO: Use add-on preferences to change default image length
# TODO: add option to add fade in and/or out by default to pictures
# TODO: add option to add default animation (ease in/out on X axis) on
class ImportLocalFootage2(bpy.types.Operator):
    bl_idname = "gdquest_vse.import_local_footage_2"
    bl_label = "Import local footage 2"
    bl_description = "Import video and audio from the project folder to VSE strips"
    bl_options = {'REGISTER', 'UNDO'}

    always_import = bpy.props.BoolProperty(
        name="Always Reimport",
        description="If true, always import all local files to new strips. \
                    If False, only import new files (check if footage has \
                    already been imported to the VSE).",
        default=False)
    keep_audio = bpy.props.BoolProperty(
        name="Keep audio from video files",
        description="If False, the audio that comes with video files will not be imported",
        default=False)
    img_length = bpy.props.IntProperty(
        name="Image strip length",
        description="Controls the duration of the imported image strips length",
        default=96,
        min=1)
    img_padding = bpy.props.IntProperty(
        name="Image strip padding",
        description="Padding added between imported image strips in frames",
        default=24,
        min=1)
    # PSD related features
    import_psd = bpy.props.BoolProperty(
        name="Import PSD as image",
        description="When True, psd files will be imported as individual image strips",
        default=False)
    ps_assets_as_img = bpy.props.BoolProperty(
        name="Import PS assets as images",
        description="Imports the content of folders generated by Photoshop's quick export \
                    function as individual image strips",
        default=True)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not bpy.data.is_saved:
            return {"CANCELLED"}

        sequencer = bpy.ops.sequencer
        context = bpy.context
        path = bpy.data.filepath

        bpy.ops.screen.animation_cancel(restore_frame=True)

        # TODO: remove after refactor
        wm = bpy.context.window_manager
        sequencer_area = {'region': wm.windows[0].screen.areas[2].regions[0],
                          'blend_data': bpy.context.blend_data,
                          'scene': bpy.context.scene,
                          'window': wm.windows[0],
                          'screen': bpy.data.screens['Video Editing'],
                          'area': bpy.data.screens['Video Editing'].areas[2]}

        # TODO: REIMPORT
        # check_strip_names = False
        channel_for_audio = 1 if self.keep_audio else 0
        empty_channel = find_empty_channel(mode='ABOVE')
        created_img_strips = []

        working_directory = get_working_directory(path)
        folders = {}

        for d in os.listdir(path=working_directory):
            if d in ProjectSettings.folders:
                folders[d] = working_directory + "\\" + d

        def find_files(directory, file_extensions, recursive=False):
            """Walks through a folder and returns files matching the extensions.
               Then, converts the files to a list of dictionaries to import in Blender"""
            if not directory and file_extensions:
                return None

            files = []

            # TODO: Ignore "_proxy" folders after coding proxy addon
            from glob import glob
            from os.path import basename

            for ext in file_extensions:
                source_pattern = directory + "\\"
                pattern = source_pattern + ext
                files.extend(glob(pattern))

                if not recursive:
                    continue
                pattern = source_pattern + "**\\" + ext
                files.extend(glob(pattern))

            files = [path for path in files if not basename(path).endswith(ProjectSettings.PROXY_STRING)]

            # TODO: Properly handle images
            # Folder containing img files = img sequence BUT
            # not for selected folders, i.e. ps/krita export folders
            # if basename(directory) == ProjectSettings.FOLDER_NAMES.IMG:

            files_list = []
            for f in files:
                dictionary = {'name': f[len(directory)+1:]}
                files_list.append(dictionary)
            return {'path': directory, 'files': files_list}

        # To add files, need a list of dictionaries like
        # {'name': 'path'} where path is relative to filepath
        audio_files = find_files(folders['audio'], Extensions.AUDIO)
        video_files = find_files(folders['video'], Extensions.VIDEO, recursive=True)
        img_files = find_files(folders['img'], Extensions.IMG, recursive=True)

        print(audio_files)
        print(video_files)
        print(img_files)

        # PROCESSING IMAGE STRIPS
        # sequencer.select_all(action='DESELECT')
        if created_img_strips:
            add_transform_effect(created_img_strips)
            for s in created_img_strips:
                s.select = True

        return {"FINISHED"}