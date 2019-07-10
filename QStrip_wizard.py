#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

from __future__ import division
import math
import copy
import pcbnew
from pcbnew import wxPoint
from pcbnew import wxSize
from pcbnew import FromMM
from pcbnew import ToMM
from pcbnew import PutOnGridMM

import FootprintWizardBase

class QStrip_FootprintWizard(FootprintWizardBase.FootprintWizard):

    def GetName(self):
        return "Samtec Q Strip Terminal"
    
    def GetDescription(self):
        return "Samtec QTE/QTS/QTH High-Speed Ground Plane Terminal Strip Wizard"
    
    def GetValue(self):
        return "Samtec_QStrip"

    def GenerateParameterList(self):
        # Fabrication/silk layer configuration
        self.AddParam("Layout", "variant", r"Terminal,Socket", r"Terminal")
        self.AddParam("Layout", "width", self.uMM, 60.00)
        self.AddParam("Layout", "height", self.uMM, 5.97)
        self.AddParam("Layout", "silkscreen offset", self.uMM, 0.25)
        # Pin bank configuration
        self.AddParam("Banks", "banks", self.uInteger, 3)
        self.AddParam("Banks", "pins per bank", self.uInteger, 60)
        self.AddParam("Banks", "differential", self.uInteger, 0)
        self.AddParam("Banks", "spacing", self.uMM, 20.0)
        self.AddParam("Banks", "width", self.uMM, 16.4)
        self.AddParam("Banks", "height", self.uMM, 3.9)
        # Signal pad parameters
        self.AddParam("Signal Pads", "pitch", self.uMM, 0.5)
        self.AddParam("Signal Pads", "width", self.uMM, 0.305)
        self.AddParam("Signal Pads", "height", self.uMM, 1.45)
        self.AddParam("Signal Pads", "y offset", self.uMM, 3.086)
        # Ground pad parameters
        self.AddParam("Ground Pads", "height", self.uMM, 0.64)
        self.AddParam("Ground Pads", "width (inner)", self.uMM, 4.7)
        self.AddParam("Ground Pads", "width (outer)", self.uMM, 2.54)
        self.AddParam("Ground Pads", "spacing (inner)", self.uMM, 6.35)
        self.AddParam("Ground Pads", "spacing (outer)", self.uMM, 16.89)
        # NPTH alignment pin parameters
        self.AddParam("Alignment Holes", "enable", self.uBool, True)
        self.AddParam("Alignment Holes", "drill", self.uMM, 1.02)
        self.AddParam("Alignment Holes", "distance", self.uMM, 58.48)
        self.AddParam("Alignment Holes", "y offset", self.uMM, 2.03)
        # PTH latching pin parameters
        self.AddParam("Locking Pins", "enable", self.uBool, False)
        self.AddParam("Locking Pins", "drill", self.uMM, 0.81)
        self.AddParam("Locking Pins", "annular ring", self.uMM, 0.5)
        self.AddParam("Locking Pins", "distance", self.uMM, 61.7)
        self.AddParam("Locking Pins", "y offset", self.uMM, 0.5)
        
    # Build a rectangular pad
    def smdRectPad(self,module,name,size,pos):
        pad = pcbnew.D_PAD(module)
        pad.SetSize(size)
        pad.SetShape(pcbnew.PAD_SHAPE_RECT)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetLayerSet(pad.SMDMask())
        pad.SetPos0(pos)
        pad.SetPosition(pos)
        pad.SetName(name)
        return pad

    # Build a hole
    def holePad(self,module,name,x,y,drill,ring = None):
        pad = pcbnew.D_PAD(module)
        pad.SetShape(pcbnew.PAD_DRILL_SHAPE_CIRCLE)
        if ring == None:
            # NPTH
            pad.SetAttribute(pcbnew.PAD_ATTRIB_HOLE_NOT_PLATED)
            pad.SetLayerSet(pad.UnplatedHoleMask())
            pad.SetSize(wxSize(drill, drill))
            pad.SetDrillSize(wxSize(drill, drill))
        else:
            # PTH
            pad.SetAttribute(pcbnew.PAD_ATTRIB_STANDARD)
            pad.SetLayerSet(pad.StandardMask())
            pad.SetSize(wxSize(drill+ring, drill+ring))
            pad.SetDrillSize(wxSize(drill, drill))
        pad.SetPos0(wxPoint(x,y))
        pad.SetPosition(wxPoint(x,y))
        pad.SetName(name)
        return pad

    def OpenMarkerArrow(self, x, y, direction, width=pcbnew.FromMM(1)):
        """!
        Draw an open marker arrow facing in the given direction, with the
        point at (x,y).
        
        @param x: x position of the arrow tip
        @param y: y position of the arrow tip
        @param direction: arrow direction in degrees (0 is "north", can use
        dir* shorthands)
        @param width: arrow width
        """
        self.draw.TransformTranslate(x, y)
        self.draw.TransformRotationOrigin(direction)

        pts = [(-width/2, width/2),
               (0,0),
               (width/2,  width/2)]
        
        self.draw.Polyline(pts)
        self.draw.PopTransform(2)
    
    def CheckParameters(self):
        pass
    
    def BuildThisFootprint(self):
        # General parameters
        param = self.parameters
        variant = param["Layout"]["variant"]
        
        # Bank parameters
        banks  = param["Banks"]["banks"]
        diff   = param["Banks"]["differential"]
        bank_x = param["Banks"]["spacing"]
        pins_per_bank = param["Banks"]["pins per bank"]

        ########################################################################
        # Copper layer(s)
        
        # Get signal pad parameters
        pitch      = param["Signal Pads"]["pitch"]
        pad_width  = param["Signal Pads"]["width"]
        pad_height = param["Signal Pads"]["height"]
        pad_y = param["Signal Pads"]["y offset"]
        pad_size = wxSize(pad_width, pad_height)
        
        # Pin 1 position
        pin1 = wxPoint(0,0)
        pin1.x = int(-(pins_per_bank / 4)*pitch + pitch/2 - ((banks-1) / 2)*bank_x)
        if variant == "Terminal":
            pin1.y = -pad_y
        elif variant == "Socket":
            pin1.y = pad_y
        
        # Bank 1 center point
        bank1_mid = pin1.x - pitch/2 + (pins_per_bank / 4)*pitch

        # Place signal pads
        n = 1 # Pin counter
        pin = [] # Pin positions, ordered by bank
        for b in range(0, banks):
            pin.append([])
            for p in range(0, pins_per_bank):
                # Compute next pad location
                pos = wxPoint(pin1.x + (p // 2)*pitch + b*bank_x,
                                     pin1.y - (p  % 2)*(2*pin1.y))
                if b < diff and ((p+1) % 6 == 0 or (p+2) % 6 == 0):
                    # Place gaps between differential pairs
                    continue
                else:
                    pin[b].append(pos) # Add position to list
                    # Create pad (both single-ended and differential)
                    pad = self.smdRectPad(self.module, str(n), pad_size, pos)
                    self.module.Add(pad)
                    n = n + 1
        
        # Ground pad parameters
        gnd_height    = param["Ground Pads"]["height"]
        gnd_width_in  = param["Ground Pads"]["width (inner)"]
        gnd_width_out = param["Ground Pads"]["width (outer)"]
        gnd_space_in  = param["Ground Pads"]["spacing (inner)"] / 2
        gnd_space_out = param["Ground Pads"]["spacing (outer)"] / 2
        gnd_space = [-gnd_space_out, -gnd_space_in, gnd_space_in, gnd_space_out]
        gnd_size  = [wxSize(gnd_width_out, gnd_height),
                     wxSize(gnd_width_in, gnd_height),
                     wxSize(gnd_width_in, gnd_height),
                     wxSize(gnd_width_out, gnd_height)]
        
        # Place ground plane pads
        for b in range(banks):
            mid = bank1_mid + b*bank_x # Bank midpoint
            for i in range(len(gnd_space)):
                pos = wxPoint(mid + gnd_space[i], 0)
                pad = self.smdRectPad(self.module, str(n), gnd_size[i], pos)
                self.module.Add(pad)
                n = n + 1

        ########################################################################
        # Holes
        align_drill = param["Alignment Holes"]["drill"]
        align_pos = wxPoint(param["Alignment Holes"]["distance"] / 2,
                            param["Alignment Holes"]["y offset"])
        
        lock_drill = param["Locking Pins"]["drill"]
        lock_ring = param["Locking Pins"]["annular ring"]
        lock_pos = wxPoint(param["Locking Pins"]["distance"] / 2,
                           param["Locking Pins"]["y offset"])

        if variant == "Terminal":
            align_pos.y = -align_pos.y
            lock_pos.y = -lock_pos.y

        # Place holes
        for m in (-1,1):
            if param["Alignment Holes"]["enable"]:
                # module,name,x,y,drill,ring = None
                hole = self.holePad(self.module, "", m*align_pos.x, align_pos.y,
                                    align_drill)
                self.module.Add(hole)
            if param["Locking Pins"]["enable"]:
                hole = self.holePad(self.module, "MH", m*lock_pos.x, lock_pos.y,
                                    lock_drill, lock_ring)
                self.module.Add(hole)

        ########################################################################
        # Fabrication (F.Fab) layer
        self.draw.SetLineThickness(FromMM(0.1)) # Default per KLC F5.2
        self.draw.SetLayer(pcbnew.F_Fab)
                                       
        # Draw connector outline
        #fab_width = banks * bank_x
        #if variant == "Socket":
        #    # Sockets are 1.27mm wider in all relevant Q Strip datasheets
        #    fab_width = fab_width + FromMM(1.27)
        
        fab_width = param["Layout"]["width"]
        fab_height = param["Layout"]["height"]
        fab_y = fab_height / 2
        leftEdge = -fab_width / 2
        chamfer = fab_height / 4 # 1/4 connector height, cosmetic only
        
        if variant == "Terminal":
            points = [(0, -fab_y),
                      (leftEdge, -fab_y),
                      (leftEdge, fab_y - chamfer),
                      (leftEdge + chamfer, fab_y),
                      (0, fab_y)]
            self.draw.Polyline(points, mirrorX = 0)
            # Pin 1 marker
            self.OpenMarkerArrow(pin1.x, (pitch-fab_height)/2, self.draw.dirS, pitch)
        elif variant == "Socket":
            # Outline
            self.draw.Box(0, 0, fab_width, fab_height)
            # Chamfers
            points = [(leftEdge, -fab_y + chamfer),
                      (leftEdge + chamfer, -fab_y)]
            self.draw.Polyline(points, mirrorX = 0)
            # Pin 1 marker
            self.OpenMarkerArrow(pin1.x, (fab_height-pitch)/2, self.draw.dirN, pitch)
        
        # Draw bank outlines
        bank_height = param["Banks"]["height"]
        bank_width = 2*gnd_space_out # Approximate, ok for cosmetic purposes
        for b in range(0,banks):
            mid = wxPoint(bank1_mid + b*bank_x, 0)
            self.draw.Box(mid.x, mid.y, bank_width, bank_height)
        
        ########################################################################
        # Silkscreen (F.SilkS) layer
        self.draw.SetLineThickness(FromMM(0.12)) # KLC5.1, per IPC-7351C
        self.draw.SetLayer(pcbnew.F_SilkS)

        # Silkscreen parameters
        silk_offset = param["Layout"]["silkscreen offset"]
        silk_grid = ToMM(silk_offset)
        silk_y = fab_y + silk_offset
        silk_leftEdge = leftEdge - silk_offset
        silk_chamfer = chamfer + silk_offset/2
        silk_pin = int(pad_width/2 + silk_offset)
        silk_pin1 = pin1.x - pad_width/2 - silk_offset

        silkEndL = [] # Left end outline
        silkEndR = [] # Right end outline (usually mirrors the left)
        if variant == "Terminal":
            silkEndL = [wxPoint(silk_pin1, -silk_y),
                        wxPoint(silk_leftEdge, -silk_y),
                        wxPoint(silk_leftEdge, silk_y - silk_chamfer),
                        wxPoint(silk_leftEdge + silk_chamfer, silk_y),
                        wxPoint(silk_pin1, silk_y)]
            # Draw Pin 1 indicator
            self.draw.Line(silk_pin1, pin1.y - pad_height/2,
                           silkEndL[0].x, silkEndL[0].y)
        elif variant == "Socket":
            silkEndL = [wxPoint(silk_pin1, silk_y),
                        wxPoint(silk_leftEdge, silk_y),
                        wxPoint(silk_leftEdge, -silk_y),
                        wxPoint(silk_pin1, -silk_y)]
            # Draw Pin 1 indicator
            r = pad_width // 2
            y = pin1.y + pad_height/2 + r + silk_offset
            self.draw.Circle(pin1.x, y, r, True)
        
        # Generate right endpoints:
        # Deep copy and mirror left endpoints about X axis, skip the first point
        for p in silkEndL:
            silkEndR.append(wxPoint(-p.x, p.y))
        
        # Define x offset from the last pin:
        # End outlines do not mirror perfectly in differential banks
        silkEndR[0].x = pin[-1][-1].x + silk_pin
        silkEndR[-1].x = pin[-1][-1].x + silk_pin
        
        # Draw silkscreen end outlines
        self.draw.Polyline(silkEndL)
        self.draw.Polyline(silkEndR)
        
        # Draw silkscreen outline along sides between banks
        for b in range(0,banks-1):
            # Last pin in current bank
            x0 = pin[b][-1].x + pad_width/2 + silk_offset
            # First pin in next bank
            x1 = pin[b+1][0].x - pad_width/2 - silk_offset
            # Draw
            for m in (-1,1):
                self.draw.Line(x0, m*silk_y, x1, m*silk_y)

        ########################################################################
        # Courtyard        
        self.draw.SetLayer(pcbnew.F_CrtYd)
        self.draw.SetLineThickness(FromMM(0.05))
        
        # Draw courtyard
        court_height = PutOnGridMM(2*(pad_y + pad_height/2), 0.01) + FromMM(1)
        court_width = PutOnGridMM(fab_width, 0.01) + FromMM(1)
        self.draw.Box(0, 0, court_width, court_height)

        ########################################################################
        # Text
        text_size = self.GetTextSize() # IPC nominal
        text_y = PutOnGridMM(pad_y + pad_height/2 + FromMM(1), 0.5)
        
        # Automatically add RefDes and Value fields
        self.draw.Reference(0, -text_y, text_size)
        self.draw.Value(0, text_y, text_size)

        # Add reference text to F.Fab
        ref = self.module.Reference().Duplicate()
        ref.SetType(ref.TEXT_is_DIVERS)
        ref.SetText(r"%R")
        ref.SetLayer(pcbnew.F_Fab)
        self.module.Add(ref)
        
        self.module.SetAttributes(pcbnew.MOD_CMS)
        
QStrip_FootprintWizard().register()
