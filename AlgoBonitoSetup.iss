; Script de Inno Setup para AlgoBonito

[Setup]
AppName=AlgoBonito
AppVersion=1.0
AppPublisher=Tu Nombre/Empresa

DefaultDirName={autopf}\AlgoBonito
DefaultGroupName=AlgoBonito
AllowNoIcons=yes
OutputBaseFilename=AlgoBonitoSetup
OutputDir="c:/Users/Cristian carrasco/Desktop/Algo Bonito/output"
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=asents\algo.ico

[Files]
Source: "dist\AlgoBonito.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "database.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "Database2.accdb"; DestDir: "{app}"; Flags: ignoreversion
Source: "main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "main_new.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "asents\*"; DestDir: "{app}\asents"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AlgoBonito"; Filename: "{app}\AlgoBonito.exe"
Name: "{autodesktop}\AlgoBonito"; Filename: "{app}\AlgoBonito.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\AlgoBonito.exe"; Description: "{cm:LaunchProgram,AlgoBonito}"; Flags: nowait postinstall skipifdoesntexist
