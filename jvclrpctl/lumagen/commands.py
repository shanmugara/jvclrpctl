"""
Lumagen Radiance Command Interface
High-level command methods for querying and controlling the Radiance
"""

import time
from typing import Optional, Dict, Any
from .connection import LumagenRadiance
from .constants import (
    CMD_QUERY_FULL_STATUS_V4, CMD_QUERY_HDR_STATUS,
    HDR_STATUS_SDR, HDR_STATUS_HDR
)
from ..logger import warn, error, debug


class LumagenCommands:
    """
    High-level command interface for Lumagen Radiance
    Wraps low-level connection methods with easy-to-use functions
    """
    
    def __init__(self, radiance: LumagenRadiance):
        """
        Initialize commands interface
        
        Args:
            radiance: Connected LumagenRadiance instance
        """
        self.radiance = radiance
    
    def get_hdr_status(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        Query HDR status (ZQI52)
        
        Args:
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            Dictionary with:
                - is_hdr (bool): True if HDR, False if SDR
                - min_luminance (float): Minimum mastering luminance
                - max_luminance (int): Maximum mastering luminance
                - max_cll (int): Maximum content light level
        """
        for attempt in range(max_retries):
            try:
                response = self.radiance.query('ZQI52')
                debug(f"Lumagen ZQI52 raw: {response!r}")

                # Per RS232 spec the ZQI52 response is "V,Min,Max,Cll" with no
                # "I52" command echo (unlike ZQI50/ZQI51). Some firmware may still
                # echo it, so strip an optional leading non-numeric token to make
                # both shapes parse identically. V is always a digit (0/1).
                parts = response.split(',')
                if parts and not parts[0].lstrip('-').isdigit():
                    parts = parts[1:]

                if len(parts) >= 4:
                    v = int(parts[0])
                    min_lum = float(parts[1])
                    max_lum = int(parts[2])
                    max_cll = int(parts[3])

                    return {
                        'is_hdr': v == HDR_STATUS_HDR,
                        'min_luminance': min_lum,
                        'max_luminance': max_lum,
                        'max_cll': max_cll,
                        'error': None
                    }
                else:
                    raise ValueError(f"Lumagen: Unexpected HDR status response format: {response}")

            except (ValueError, IndexError) as e:
                if attempt < max_retries - 1:
                    warn(f"Lumagen: Failed to parse HDR status (attempt {attempt + 1}/{max_retries}): {e}. Retrying in 1 second...")
                    time.sleep(1)
                else:
                    error(f"Lumagen: Failed to parse HDR status after {max_retries} attempts: {e}")
                    return {
                        'is_hdr': False,
                        'min_luminance': 0.0,
                        'max_luminance': 0,
                        'max_cll': 0,
                        'error': str(e)
                    }
        # If all retries fail without raising an exception, return error
        return {
            'is_hdr': False,
            'min_luminance': 0.0,
            'max_luminance': 0,
            'max_cll': 0,
            'error': "Failed to get HDR status, max retries exceeded"
        }
    
    def get_full_status_v4(self) -> Dict[str, Any]:
        """
        Query comprehensive status (ZQI24)
        
        Returns:
            Dictionary with parsed status information including:
                - input_status: 0=no source, 1=active video, 2=internal pattern
                - source_rate: Vertical refresh rate
                - source_resolution: Vertical resolution
                - is_hdr: True if HDR source
                - source_aspect: Source content aspect ratio
                - output_resolution: Output vertical resolution
                - and many more fields...
        """
        response = self.radiance.query('ZQI24')
        
        # Response format (very long):
        # !I24,M,RRR,VVVV,D,X,AAA,SSS,Y,T,WWWW,C,B,PPP,QQQQ,ZZZ,E,F,G,H,II,KK,JJJ,LLL
        parts = response.split(',')
        
        if len(parts) < 20:
            return {}
        
        try:
            status = {
                'input_status': int(parts[1]),  # M
                'source_rate': int(parts[2]),   # RRR
                'source_resolution': int(parts[3]),  # VVVV
                'source_3d_mode': int(parts[4]),  # D
                'input_config': int(parts[5]),  # X
                'source_raster_aspect': int(parts[6]),  # AAA
                'source_aspect': int(parts[7]),  # SSS
                'nls_active': parts[8] == 'N',  # Y
                'output_3d_mode': int(parts[9]),  # T
                'outputs_on': parts[10],  # WWWW (hex)
                'cms_active': int(parts[11]),  # C
                'style_active': int(parts[12]),  # B
                'output_rate': int(parts[13]),  # PPP
                'output_resolution': int(parts[14]),  # QQQQ
                'output_aspect': int(parts[15]),  # ZZZ
                'output_colorspace': int(parts[16]),  # E (0=601, 1=709, 2=2020, 3=2100)
                'is_hdr': int(parts[17]) == HDR_STATUS_HDR,  # F (0=SDR, 1=HDR)
                'source_mode': parts[18],  # G (i=interlaced, p=progressive, -=no input)
                'output_mode': parts[19],  # H (I=interlaced, P=progressive)
            }
            
            # Optional fields
            if len(parts) > 20:
                status['virtual_input'] = int(parts[20])  # II
            if len(parts) > 21:
                status['physical_input'] = int(parts[21])  # KK
            if len(parts) > 22:
                status['detected_raster_aspect'] = int(parts[22])  # JJJ
            if len(parts) > 23:
                status['detected_source_aspect'] = int(parts[23])  # LLL
            
            return status
            
        except (ValueError, IndexError) as e:
            error(f"Error parsing status: {e}")
            return {}
    
    def is_hdr(self) -> bool:
        """
        Simple check if current source is HDR
        
        Returns:
            True if HDR, False if SDR
        """
        status = self.get_hdr_status()
        return status.get('is_hdr', False)
    
    def get_alive_status(self) -> bool:
        """
        Check if Radiance is responding
        
        Returns:
            True if alive
        """
        try:
            response = self.radiance.query('ZQS00')
            return 'Ok' in response or 'S00' in response
        except:
            return False
    
    def get_device_info(self) -> Dict[str, str]:
        """
        Get device identification
        
        Returns:
            Dictionary with model, firmware, model number, serial number
        """
        response = self.radiance.query('ZQS01')
        
        # Response format: !S01,ModelName,FirmwareRev,ModelNum,SerialNum
        parts = response.split(',')
        
        if len(parts) >= 5:
            return {
                'model': parts[1],
                'firmware': parts[2],
                'model_number': parts[3],
                'serial_number': parts[4]
            }
        
        return {}
    
    def get_power_status(self) -> str:
        """
        Query power status
        
        Returns:
            'on' or 'off'
        """
        response = self.radiance.query('ZQS02')
        
        if '1' in response:
            return 'on'
        elif '0' in response:
            return 'off'
        
        return 'unknown'
