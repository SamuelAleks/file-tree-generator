#define MyAppName "File Tree Generator"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "Paape Companies"
#define MyAppURL "https://github.com/SamuelAleks/file-tree-generator"
#define MyAppExeName "FileTreeGenerator.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".ftg"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Basic settings
AppId={{EB9A771F-BC13-4A5C-B4D9-27D1EA9CCA2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Destination settings
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; Compression and output
OutputDir=installer
OutputBaseFilename=FileTreeGenerator_Setup
Compression=lzma
SolidCompression=yes

; Appearance and behavior
SetupIconFile=resources\icon.ico
WizardStyle=modern
WizardSmallImageFile=resources\icon_small.bmp
WizardImageFile=resources\wizard_image.bmp
WizardImageStretch=no
WizardImageBackColor=$FFFFFF
DisableWelcomePage=no

; Files and permissions
LicenseFile=docs\LICENSE.txt
InfoBeforeFile=docs\README.txt
InfoAfterFile=
PrivilegesRequiredOverridesAllowed=dialog
PrivilegesRequired=lowest

; Windows settings
MinVersion=10.0.14393
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsTaskSelected('portablemode')
Name: "portablemode"; Description: "Portable Mode (store settings in application folder)"; GroupDescription: "Installation Mode:"; Flags: unchecked

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "docs\README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "docs\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

; Resources (optional)
Source: "resources\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Add this key to set portable mode
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "PortableMode"; ValueData: "1"; Flags: uninsdeletekey; Tasks: portablemode

[Code]
// This function creates a batch file to support portable mode if selected
procedure CreatePortableModeFile;
var
  FileName: string;
  BatchFile: TStringList;
begin
  if IsTaskSelected('portablemode') then
  begin
    FileName := ExpandConstant('{app}\portable_mode.bat');
    BatchFile := TStringList.Create;
    try
      BatchFile.Add('@echo off');
      BatchFile.Add('echo Setting up portable mode...');
      BatchFile.Add('if not exist "%~dp0settings" mkdir "%~dp0settings"');
      BatchFile.Add('set USERPROFILE=%~dp0settings');
      BatchFile.Add('start "" "%~dp0FileTreeGenerator.exe"');
      BatchFile.SaveToFile(FileName);
    finally
      BatchFile.Free;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    CreatePortableModeFile;
  end;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo, MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  S: String;
begin
  S := '';
  S := S + 'Welcome to the File Tree Generator setup wizard.' + NewLine + NewLine;
  S := S + MemoDirInfo + NewLine;
  S := S + MemoGroupInfo + NewLine;
  S := S + MemoTasksInfo + NewLine;

  if IsTaskSelected('portablemode') then
    S := S + NewLine + 'PORTABLE MODE: Settings will be stored in the application folder.' + NewLine;

  Result := S;
end;